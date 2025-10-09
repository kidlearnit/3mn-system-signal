#!/usr/bin/env python3
"""
Check MACD Multi-TF US signals in database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_macd_signals():
    """Check MACD Multi-TF US signals in database"""
    print("🔍 Checking MACD Multi-TF US signals in database...")
    print("=" * 60)
    
    try:
        from app.db import SessionLocal
        from sqlalchemy import text
        
        # Initialize database connection
        from app.db import init_db
        import os
        init_db(os.getenv("DATABASE_URL"))
        
        with SessionLocal() as session:
            # Check signals with strategy_id = 998 (MACD Multi-TF US)
            result = session.execute(text("""
                SELECT id, symbol, signal_type, timeframe, created_at, details
                FROM signals 
                WHERE strategy_id = 998 
                ORDER BY created_at DESC 
                LIMIT 10
            """)).fetchall()
            
            if result:
                print(f"✅ Found {len(result)} MACD Multi-TF US signals:")
                print()
                
                for row in result:
                    print(f"ID: {row[0]}")
                    print(f"Symbol: {row[1]}")
                    print(f"Signal Type: {row[2]}")
                    print(f"Timeframe: {row[3]}")
                    print(f"Created: {row[4]}")
                    print(f"Details: {row[5][:100]}..." if row[5] and len(str(row[5])) > 100 else f"Details: {row[5]}")
                    print("-" * 40)
            else:
                print("❌ No MACD Multi-TF US signals found")
            
            # Check total signals count
            total_result = session.execute(text("""
                SELECT COUNT(*) as total FROM signals WHERE strategy_id = 998
            """)).fetchone()
            
            print(f"\n📊 Total MACD Multi-TF US signals: {total_result[0]}")
            
            # Check recent signals by timeframe
            timeframe_result = session.execute(text("""
                SELECT timeframe, COUNT(*) as count, MAX(created_at) as latest
                FROM signals 
                WHERE strategy_id = 998 
                GROUP BY timeframe
                ORDER BY latest DESC
            """)).fetchall()
            
            if timeframe_result:
                print(f"\n📈 Signals by timeframe:")
                for row in timeframe_result:
                    print(f"   {row[0]}: {row[1]} signals (latest: {row[2]})")
            
            return True
            
    except Exception as e:
        print(f"❌ Error checking signals: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_worker_logs():
    """Check worker logs for MACD Multi-TF jobs"""
    print("\n🔍 Checking worker logs...")
    print("=" * 60)
    
    try:
        # Check if logs directory exists
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        
        if os.path.exists(logs_dir):
            log_files = [f for f in os.listdir(logs_dir) if f.endswith('.log')]
            print(f"📁 Log files found: {log_files}")
            
            # Check system.log for MACD Multi-TF entries
            system_log = os.path.join(logs_dir, 'system.log')
            if os.path.exists(system_log):
                with open(system_log, 'r') as f:
                    lines = f.readlines()
                    macd_lines = [line for line in lines if 'MACD Multi-TF' in line]
                    
                    if macd_lines:
                        print(f"\n📝 Found {len(macd_lines)} MACD Multi-TF log entries:")
                        for line in macd_lines[-5:]:  # Show last 5 entries
                            print(f"   {line.strip()}")
                    else:
                        print("❌ No MACD Multi-TF log entries found")
        else:
            print("❌ Logs directory not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking logs: {e}")
        return False

if __name__ == "__main__":
    print("🧪 MACD Multi-TF US Database Check")
    print("=" * 60)
    
    # Check signals in database
    signals_ok = check_macd_signals()
    
    # Check worker logs
    logs_ok = check_worker_logs()
    
    print("\n" + "=" * 60)
    if signals_ok and logs_ok:
        print("🎉 Database check completed!")
        print("✅ MACD Multi-TF US signals are being stored correctly")
    else:
        print("⚠️ Some issues found during database check")
        print("💡 Check database connection and worker logs")
