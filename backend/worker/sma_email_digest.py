#!/usr/bin/env python3
"""
SMA Email Digest Worker

Every 5 minutes (configurable), compile latest SMA signals for a configured list of
symbols and send an HTML table email via the shared EmailService.

Configuration via environment variables:
  - DATABASE_URL: SQLAlchemy URL
  - EMAIL_ADDRESS, EMAIL_PASSWORD, EMAIL_TO, SMTP_HOST, SMTP_PORT: see EmailService
  - EMAIL_DIGEST_SYMBOLS: comma-separated tickers to include; if empty, use top active
  - EMAIL_DIGEST_LIMIT: max rows in table (default 25)
  - EMAIL_DIGEST_INTERVAL_SECONDS: interval between sends (default 300)
  - EMAIL_DIGEST_TIMEFRAMES: list of TFs to include, comma-separated (default: 1m,2m,5m,15m)
  - ONESHOT=1 to run once and exit (for testing)
"""

import os
import time
import logging
from typing import List, Tuple

import pandas as pd
from sqlalchemy import text

import app.db as db
from app.services.email_service import email_service
from worker.sma_jobs import job_sma_pipeline
from utils.market_time import is_market_open


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_symbols_to_monitor() -> List[Tuple[int, str, str]]:
    symbols_env = os.getenv("EMAIL_DIGEST_SYMBOLS", "").strip()
    limit = int(os.getenv("EMAIL_DIGEST_SYMBOL_LIMIT", os.getenv("EMAIL_DIGEST_LIMIT", "25")))
    with db.SessionLocal() as s:
        if symbols_env:
            tickers = [t.strip() for t in symbols_env.split(",") if t.strip()]
            if not tickers:
                return []
            rows: List[Tuple[int, str, str]] = []
            # Query per ticker for portability
            for t in tickers:
                row = s.execute(text(
                    "SELECT id, ticker, exchange FROM symbols WHERE ticker = :t AND active=1 LIMIT 1"
                ), {"t": t}).fetchone()
                if row:
                    rows.append((row[0], row[1], row[2]))
            return rows[:limit]
        # fallback: top active
        rows = s.execute(text(
            "SELECT id, ticker, exchange FROM symbols WHERE active=1 ORDER BY id LIMIT :lim"
        ), {"lim": limit}).fetchall()
        return [(sid, tck, ex) for sid, tck, ex in rows]


def _get_latest_sma_signal_for_symbol(symbol_id: int, timeframes: List[str]):
    with db.SessionLocal() as s:
        results = []
        for tf in timeframes:
            row = s.execute(text(
                """
                SELECT timeframe, timestamp, signal_type, signal_direction, signal_strength,
                       current_price, ma18, ma36, ma48, ma144, avg_ma
                FROM sma_signals
                WHERE symbol_id = :sid AND timeframe = :tf
                ORDER BY timestamp DESC
                LIMIT 1
                """
            ), {"sid": symbol_id, "tf": tf}).mappings().first()
            if row:
                results.append(row)
        return results


def _build_html_table(rows: List[dict]) -> str:
    # Create a DataFrame for nice formatting and sorting
    if not rows:
        return "<p>No SMA signals found.</p>"
    df = pd.DataFrame(rows)
    # Order columns for readability
    # Minimal, prediction-oriented view (hide raw MA values)
    ordered_cols = [
        "ticker", "exchange", "timeframe", "trend", "signal_type", "signal_strength",
        "current_price", "timestamp"
    ]
    for col in ordered_cols:
        if col not in df.columns:
            df[col] = ""
    df = df[ordered_cols]
    # Basic styling
    styles = (
        "table { border-collapse: collapse; width: 100%; }"
        "th, td { border: 1px solid #ddd; padding: 6px; font-family: Arial, sans-serif; font-size: 12px; }"
        "th { background: #f4f6f8; text-align: left; }"
        ".bull { color: #0ea5e9; font-weight: 600; }"
        ".bear { color: #ef4444; font-weight: 600; }"
    )
    # Apply classes for signal coloring
    def _sig_class(sig: str) -> str:
        if sig and "bear" in sig:
            return "bear"
        if sig and "bull" in sig:
            return "bull"
        return ""
    html_rows = []
    html_rows.append("<table>")
    html_rows.append("<thead><tr>" + "".join(f"<th>{c}</th>" for c in ordered_cols) + "</tr></thead>")
    html_rows.append("<tbody>")
    for _, r in df.iterrows():
        sig_type = str(r.get("signal_type", ""))
        css = _sig_class(sig_type)
        tds = []
        for c in ordered_cols:
            val = r.get(c, "")
            if c in ("signal_type", "signal_direction") and css:
                tds.append(f"<td class='{css}'>{val}</td>")
            else:
                tds.append(f"<td>{val}</td>")
        html_rows.append("<tr>" + "".join(tds) + "</tr>")
    html_rows.append("</tbody></table>")
    return f"<style>{styles}</style>" + "".join(html_rows)


def _collect_digest_rows() -> List[dict]:
    timeframes = [tf.strip() for tf in os.getenv("EMAIL_DIGEST_TIMEFRAMES", "1m,2m,5m,15m").split(",") if tf.strip()]
    limit = int(os.getenv("EMAIL_DIGEST_LIMIT", "25"))
    monitor = _get_symbols_to_monitor()
    rows: List[dict] = []
    
    for sid, ticker, exchange in monitor:
        # Only process symbols whose market is currently open
        try:
            market_open, _, _ = is_market_open(exchange)
            if not market_open:
                logger.debug(f"Skipping {ticker} ({exchange}) - market closed")
                continue
        except Exception as e:
            logger.warning(f"Could not check market status for {ticker} ({exchange}): {e}")
            # Proceed if we can't determine market status
        
        latest = _get_latest_sma_signal_for_symbol(sid, timeframes)
        for item in latest:
            sig_type = item.get("signal_type", "")
            # include local_bullish/bearish and confirmed/triple
            if not any(k in sig_type for k in ["local_bullish", "local_bearish", "confirmed", "triple_"]):
                continue
            # Derive short trend label
            if "bear" in sig_type:
                trend = "Down"
            elif "bull" in sig_type:
                trend = "Up"
            else:
                trend = "Sideways"
            rows.append({
                "ticker": ticker,
                "exchange": exchange,
                "trend": trend,
                **item
            })
            if len(rows) >= limit:
                return rows
    return rows


def _get_int_env(name: str, default_value: int) -> int:
    raw = os.getenv(name)
    if raw is None or str(raw).strip() == "":
        return default_value
    try:
        return int(str(raw).strip())
    except Exception:
        return default_value


def run_once() -> bool:
    # Only run when ANY monitored market is open
    try:
        symbols = _get_symbols_to_monitor()
        if not symbols:
            logger.info("No symbols to monitor; skipping digest send.")
            return False
        
        # Check if any market is open
        markets_open = False
        for sid, ticker, exchange in symbols:
            market_open, _, _ = is_market_open(exchange)
            if market_open:
                markets_open = True
                break
        
        if not markets_open:
            logger.info("All monitored markets are closed; skipping digest send.")
            return False
            
    except Exception as e:
        # If we can't determine, proceed but log
        logger.warning(f"Market status check failed: {e}; proceeding with digest.")
    if not email_service.is_configured():
        logger.warning("Email service not configured; skipping digest send")
        return False
    # Refresh latest signals by running pipeline for monitored symbols (only for open markets)
    symbols = _get_symbols_to_monitor()
    for sid, ticker, exchange in symbols:
        try:
            # Only run pipeline for symbols whose market is open
            market_open, _, _ = is_market_open(exchange)
            if market_open:
                job_sma_pipeline(sid, ticker, exchange)
                logger.debug(f"Ran SMA pipeline for {ticker} ({exchange}) - market open")
            else:
                logger.debug(f"Skipped SMA pipeline for {ticker} ({exchange}) - market closed")
        except Exception as e:
            logger.warning("Pipeline failed for %s: %s", ticker, e)
            continue
    rows = _collect_digest_rows()
    html = _build_html_table(rows)
    subject = os.getenv("EMAIL_DIGEST_SUBJECT", "SMA Digest")
    ok = email_service.send(subject, body_text="SMA Digest (HTML) attached", body_html=html)
    logger.info("Digest sent: %s", ok)
    return ok


def main():
    db.init_db(os.getenv("DATABASE_URL"))
    oneshot = os.getenv("ONESHOT") == "1"
    interval = _get_int_env("EMAIL_DIGEST_INTERVAL_SECONDS", 300)
    if oneshot:
        run_once()
        return
    logger.info("Starting SMA email digest loop; interval=%s seconds", interval)
    while True:
        try:
            run_once()
        except Exception as e:
            logger.error("Digest error: %s", e)
        time.sleep(interval)


if __name__ == "__main__":
    main()


