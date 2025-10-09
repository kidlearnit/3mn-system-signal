import os
import json
from typing import Set

from sqlalchemy import text

import app.db as db


def count_vn_symbols_in_25symbols() -> int:
    db.init_db(os.getenv("DATABASE_URL"))
    vn_exchanges: Set[str] = {"HOSE", "HNX", "UPCOM"}
    count = 0

    with db.SessionLocal() as s:
        row = s.execute(
            text(
                """
                SELECT id, nodes, properties FROM workflows
                WHERE name=:name AND status='active'
                LIMIT 1
                """
            ),
            {"name": "25symbols"},
        ).fetchone()

        if not row:
            print("No active 25symbols workflow found")
            return 0

        wf_id, nodes_json, props_json = row
        try:
            nodes = json.loads(nodes_json)
        except Exception:
            nodes = []

        try:
            properties = json.loads(props_json) if props_json else {}
        except Exception:
            properties = {}

        for node in nodes:
            if not isinstance(node, dict):
                continue
            if node.get("type") != "macd-multi":
                continue

            node_id = node.get("id")
            if not node_id:
                continue

            node_cfg = properties.get(node_id, {}) if isinstance(properties, dict) else {}
            thresholds = node_cfg.get("symbolThresholds") or []
            if not isinstance(thresholds, list):
                continue

            for item in thresholds:
                if not isinstance(item, dict):
                    continue
                symbol = str(item.get("symbol", "")).upper()
                sector = str(item.get("sector", "")).upper()
                exchange = str(item.get("exchange", "")).upper()

                is_vn = False
                if symbol.endswith(".VN"):
                    is_vn = True
                elif sector == "VN":
                    is_vn = True
                elif exchange in vn_exchanges:
                    is_vn = True

                if is_vn:
                    count += 1

    return count


if __name__ == "__main__":
    c = count_vn_symbols_in_25symbols()
    print(c)


