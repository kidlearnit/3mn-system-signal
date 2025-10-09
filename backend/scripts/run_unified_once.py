#!/usr/bin/env python3
import os
import json
import argparse
from sqlalchemy import text
import app.db as db_mod
from worker.macd_multi_unified_jobs import job_macd_multi_unified_pipeline


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="realtime", choices=["realtime", "backfill"], help="Pipeline mode")
    args = parser.parse_args()
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        db_url = (
            f"mysql+pymysql://{os.getenv('MYSQL_USER','trader')}:{os.getenv('MYSQL_PASSWORD','traderpass')}@"
            f"{os.getenv('MYSQL_HOST','mysql')}:{os.getenv('MYSQL_PORT','3306')}/"
            f"{os.getenv('MYSQL_DATABASE', os.getenv('MYSQL_DB','trading_db'))}"
        )

    db_mod.init_db(db_url)
    SessionLocal = db_mod.SessionLocal

    with SessionLocal() as s:
        rows = s.execute(
            text(
                "SELECT id,name,nodes,properties FROM workflows WHERE name LIKE :n ORDER BY updated_at DESC LIMIT 1"
            ),
            {"n": "%25symbols%"},
        ).fetchall()
        if not rows:
            print("No workflow named like 25symbols found")
            return

        wid, wname, nodes_json, props_json = rows[0]
        nodes = json.loads(nodes_json or "[]")
        props = json.loads(props_json or "{}")

        macd_nodes = [n for n in nodes if isinstance(n, dict) and n.get("type") == "macd-multi"]
        if not macd_nodes:
            print("No macd-multi node in workflow")
            return

        node_id = macd_nodes[0]["id"]
        node_conf = props.get(node_id, {})

        # Merge symbols if defined on symbol node
        if "symbolThresholds" not in node_conf:
            sym_nodes = [n for n in nodes if isinstance(n, dict) and n.get("type") == "symbol"]
            if sym_nodes:
                sym_conf = props.get(sym_nodes[0]["id"], {})
                syms = sym_conf.get("symbols", [])
                if syms:
                    node_conf = dict(node_conf)
                    node_conf["symbolThresholds"] = syms

        print("Running unified pipeline for workflow:", wname)
        res = job_macd_multi_unified_pipeline(node_conf, mode=args.mode)
        if isinstance(res, dict):
            print("status:", res.get("status"))
            print("symbols_processed:", res.get("symbols_processed"))
            print("signals_generated:", res.get("signals_generated"))
        else:
            print("result:", res)


if __name__ == "__main__":
    main()


