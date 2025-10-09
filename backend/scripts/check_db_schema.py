#!/usr/bin/env python3
"""
Script to check database schema for timeframe enum values
"""

import os
import sys
sys.path.append('/code')

from app.db import init_db, SessionLocal
from sqlalchemy import text

def check_timeframe_enum():
    """Check the actual timeframe enum values in database"""
    try:
        # Initialize database
        init_db(os.getenv("DATABASE_URL"))
        
        # Re-import SessionLocal after initialization
        from app.db import SessionLocal
        
        with SessionLocal() as session:
            # Check signals table timeframe column
            result = session.execute(text("""
                SELECT COLUMN_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME='signals' AND COLUMN_NAME='timeframe'
            """)).fetchone()
            
            if result:
                print(f"📊 Signals table timeframe column type: {result[0]}")
            else:
                print("❌ No timeframe column found in signals table")
            
            # Check existing signals with different timeframes
            result = session.execute(text("""
                SELECT DISTINCT timeframe, COUNT(*) as count
                FROM signals 
                GROUP BY timeframe
                ORDER BY timeframe
            """)).fetchall()
            
            print(f"\n📈 Existing timeframe values in signals table:")
            for timeframe, count in result:
                print(f"  - {timeframe}: {count} signals")
            
            # Check candles_tf table timeframe column
            result = session.execute(text("""
                SELECT COLUMN_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME='candles_tf' AND COLUMN_NAME='timeframe'
            """)).fetchone()
            
            if result:
                print(f"\n📊 Candles_tf table timeframe column type: {result[0]}")
            
            # Check existing candles with different timeframes
            result = session.execute(text("""
                SELECT DISTINCT timeframe, COUNT(*) as count
                FROM candles_tf 
                GROUP BY timeframe
                ORDER BY timeframe
            """)).fetchall()
            
            print(f"\n📈 Existing timeframe values in candles_tf table:")
            for timeframe, count in result:
                print(f"  - {timeframe}: {count} candles")
                
    except Exception as e:
        print(f"❌ Error checking database schema: {e}")

if __name__ == "__main__":
    check_timeframe_enum()
