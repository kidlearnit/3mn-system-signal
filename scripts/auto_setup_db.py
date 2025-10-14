#!/usr/bin/env python3
import os
import time
from pathlib import Path
from app.db import init_db, SessionLocal

def main():
    init_db(os.getenv("DATABASE_URL"))
    # Optionally run migration file at project root
    mig = Path("database_migration.sql")
    if mig.exists():
        with SessionLocal() as s, open(mig, "r", encoding="utf-8") as f:
            sql = f.read()
            for stmt in [x.strip() for x in sql.split(";") if x.strip()]:
                try:
                    s.execute(stmt)
                except Exception:
                    pass
            s.commit()
    print("✅ Auto DB setup done")

if __name__ == "__main__":
    # Wait a bit for MySQL
    time.sleep(2)
    main()


