#!/usr/bin/env python3
"""
Check recent MACD Multi-TF signals
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_recent_signals():
    """Check recent signals in database"""
    print("🔍 Checking Recent MACD Multi-TF Signals")
    print("=" * 60)
    
    try:
        from app.db import init_db, SessionLocal
        from sqlalchemy import text
        
        # Initialize database
        database_url = os.getenv("DATABASE_URL", "mysql+pymysql://trading:trading123@mysql:3306/trading")
        init_db(database_url)
        
        with SessionLocal() as s:
            # Count total signals
            result = s.execute(text("SELECT COUNT(*) FROM signals WHERE strategy_id = 1")).fetchone()
            print(f"📊 Total signals with strategy_id=1: {result[0]}")
            
            # Get recent signals
            result = s.execute(text("""
                SELECT s.id, s.symbol_id, s.signal_type, s.ts, sym.ticker
                FROM signals s
                JOIN symbols sym ON s.symbol_id = sym.id
                WHERE s.strategy_id = 1
                ORDER BY s.ts DESC
                LIMIT 10
            """)).fetchall()
            
            print(f"\n📋 Recent signals:")
            for row in result:
                signal_id, symbol_id, signal_type, ts, ticker = row
                print(f"   {ticker} (ID: {symbol_id}): {signal_type} at {ts}")
            
            # Check if any signals were generated today
            result = s.execute(text("""
                SELECT COUNT(*) FROM signals 
                WHERE strategy_id = 1 
                AND DATE(ts) = CURDATE()
            """)).fetchone()
            
            print(f"\n📅 Signals generated today: {result[0]}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_recent_signals()
    
    if success:
        print("\n✅ Signal check completed!")
    else:
        print("\n❌ Signal check failed!")
