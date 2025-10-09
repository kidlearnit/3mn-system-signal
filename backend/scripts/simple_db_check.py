#!/usr/bin/env python3
"""
Simple database check for MACD Multi-TF US signals
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_signals():
    """Check signals in database"""
    print("🔍 Checking signals in database...")
    
    try:
        from app.db import init_db
        import os
        # Use localhost for host machine
        database_url = os.getenv("DATABASE_URL", "mysql+pymysql://root:123456@localhost:3309/trading_signals")
        init_db(database_url)
        
        from app.db import SessionLocal
        from sqlalchemy import text
        
        with SessionLocal() as session:
            # Check recent signals
            result = session.execute(text("""
                SELECT id, symbol_id, signal_type, timeframe, strategy_id, ts
                FROM signals 
                ORDER BY ts DESC 
                LIMIT 10
            """)).fetchall()
            
            if result:
                print(f"✅ Found {len(result)} recent signals:")
                for row in result:
                    print(f"   ID: {row[0]}, Symbol: {row[1]}, Type: {row[2]}, TF: {row[3]}, Strategy: {row[4]}, Time: {row[5]}")
            else:
                print("❌ No signals found")
            
            # Check total count
            count_result = session.execute(text("SELECT COUNT(*) FROM signals")).fetchone()
            print(f"\n📊 Total signals: {count_result[0]}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Simple Database Check")
    print("=" * 40)
    
    success = check_signals()
    
    if success:
        print("\n✅ Database check completed!")
    else:
        print("\n❌ Database check failed!")
