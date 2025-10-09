#!/usr/bin/env python3
import os
import json
import argparse
from typing import List, Dict, Any

from sqlalchemy import text
from rq import Queue
import redis

import app.db as db_mod
from worker.macd_multi_us_jobs import job_macd_multi_us_workflow_executor
from worker.multi_indicator_jobs import job_multi_indicator_workflow_executor


def main() -> None:
    parser = argparse.ArgumentParser(description="Activate a workflow and enqueue its jobs")
    parser.add_argument("--name", required=True, help="Workflow name (substring match)")
    args = parser.parse_args()

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Fallback compose-style variables
        mysql_user = os.getenv("MYSQL_USER", "trader")
        mysql_pass = os.getenv("MYSQL_PASSWORD", "traderpass")
        mysql_host = os.getenv("MYSQL_HOST", "mysql")
        mysql_port = os.getenv("MYSQL_PORT", "3306")
        mysql_db = os.getenv("MYSQL_DATABASE", os.getenv("MYSQL_DB", "trading_db"))
        db_url = f"mysql+pymysql://{mysql_user}:{mysql_pass}@{mysql_host}:{mysql_port}/{mysql_db}"
    db_mod.init_db(db_url)

    # Access SessionLocal from module after init
    SessionLocal = db_mod.SessionLocal
    with SessionLocal() as session:
        rows = session.execute(
            text(
                """
                SELECT id, name, status, nodes, properties
                FROM workflows
                WHERE name LIKE :n
                ORDER BY updated_at DESC
                """
            ),
            {"n": f"%{args.name}%"},
        ).fetchall()

        print(f"Found {len(rows)} workflows matching '{args.name}'")
        if not rows:
            all_rows = session.execute(
                text("SELECT id, name, status FROM workflows ORDER BY updated_at DESC LIMIT 20")
            ).fetchall()
            print("Available workflows:")
            for rid, nm, st in all_rows:
                print(f"- {rid} | {nm} | {st}")
            return

        wid, wname, status, nodes_json, props_json = rows[0]
        session.execute(text("UPDATE workflows SET status='active' WHERE id=:id"), {"id": wid})
        session.commit()
        print(f"Activated: {wid} | {wname}")

        try:
            nodes: List[Dict[str, Any]] = json.loads(nodes_json or "[]")
        except Exception:
            nodes = []
        try:
            props: Dict[str, Any] = json.loads(props_json or "{}")
        except Exception:
            props = {}

        r = redis.from_url(os.getenv("REDIS_URL"))
        q = Queue("priority", connection=r)

        # Enqueue MACD Multi jobs
        macd_nodes = [n for n in nodes if isinstance(n, dict) and n.get("type") == "macd-multi"]
        for n in macd_nodes:
            node_id = n.get("id")
            node_conf = props.get(node_id, {})
            job = q.enqueue(
                job_macd_multi_us_workflow_executor,
                wid,
                node_id,
                node_conf,
                "realtime",
                job_timeout=600,
            )
            print(f"Enqueued MACD job: {job.id} for node {node_id}")

        # Enqueue Multi-Indicator jobs
        agg_nodes = [n for n in nodes if isinstance(n, dict) and n.get("type") == "aggregation"]
        symbol_nodes = [n for n in nodes if isinstance(n, dict) and n.get("type") == "symbol"]
        symbol_props = props.get(symbol_nodes[0]["id"], {}) if symbol_nodes else {}
        for n in agg_nodes:
            node_id = n.get("id")
            node_conf = props.get(node_id, {})
            combined = {
                "symbolThresholds": symbol_props.get("symbols", []),
                "aggregation": node_conf,
            }
            job = q.enqueue(
                job_multi_indicator_workflow_executor,
                wid,
                node_id,
                combined,
                "realtime",
                job_timeout=900,
            )
            print(f"Enqueued Multi-Indicator job: {job.id} for node {node_id}")


if __name__ == "__main__":
    main()


