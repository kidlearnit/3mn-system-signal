#!/usr/bin/env python3
"""
Backfill candles (1m) and SMA indicators for a batch of symbols.

Symbols are read from EMAIL_DIGEST_SYMBOLS env (comma-separated). If a symbol
doesn't exist in the DB, it will be inserted as active with exchange inferred
as NASDAQ by default.

Usage (inside container):
  python worker/backfill_batch.py  # uses defaults: days=365

Env vars:
  BACKFILL_DAYS (default 365)
  DEFAULT_EXCHANGE (default 'NASDAQ')
"""

import os
import logging
from sqlalchemy import text

import app.db as db
from worker.jobs import job_backfill_symbol
from worker.sma_jobs import job_sma_backfill


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _ensure_symbol(session, ticker: str, exchange: str):
    row = session.execute(text(
        "SELECT id, ticker, exchange FROM symbols WHERE ticker = :t LIMIT 1"
    ), {"t": ticker}).fetchone()
    if row:
        return row[0], row[1], row[2]
    session.execute(text(
        "INSERT INTO symbols (ticker, exchange, active) VALUES (:t, :ex, 1)"
    ), {"t": ticker, "ex": exchange})
    session.commit()
    sid = session.execute(text(
        "SELECT id FROM symbols WHERE ticker = :t LIMIT 1"
    ), {"t": ticker}).scalar()
    logger.info("Inserted symbol %s (%s) id=%s", ticker, exchange, sid)
    return sid, ticker, exchange


def job_backfill_batch(days: int | None = None) -> int:
    db.init_db(os.getenv("DATABASE_URL"))
    tickers_env = os.getenv("EMAIL_DIGEST_SYMBOLS", "").strip()
    if not tickers_env:
        logger.error("EMAIL_DIGEST_SYMBOLS is empty; nothing to backfill")
        return 1
    tickers = [t.strip() for t in tickers_env.split(",") if t.strip()]
    days_val = int(os.getenv("BACKFILL_DAYS", str(days if days is not None else 365)))
    default_ex = os.getenv("DEFAULT_EXCHANGE", "NASDAQ")

    with db.SessionLocal() as s:
        for t in tickers:
            try:
                sid, ticker, ex = _ensure_symbol(s, t, default_ex)
                logger.info("[Backfill] %s (%s) days=%s", ticker, ex, days_val)
                # Backfill 1m candles (auto chooses data source)
                job_backfill_symbol(sid, ticker, ex, days=days_val, source="auto")
                # Backfill SMA across TFs
                job_sma_backfill(sid, ticker, ex, days=days_val)
            except Exception as e:
                logger.exception("Backfill failed for %s: %s", t, e)
                continue
    logger.info("Batch backfill completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(job_backfill_batch())


