#!/usr/bin/env python3
"""
Debug MACD Multi-TF error
"""

import os
import sys
import traceback

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def debug_macd_error():
    """Debug MACD error"""
    
    print("🔍 DEBUGGING MACD Multi-TF Error")
    print("=" * 50)
    
    try:
        # Test 1: Import modules
        print("1. Testing imports...")
        from app.db import SessionLocal, init_db
        print("✅ Database imports OK")
        
        from worker.macd_multi_us_jobs import _process_symbol_macd_multi
        print("✅ MACD jobs import OK")
        
        # Test 2: Initialize database
        print("\n2. Testing database initialization...")
        init_db(os.getenv("DATABASE_URL"))
        print("✅ Database initialization OK")
        
        # Test 3: Test SessionLocal
        print("\n3. Testing SessionLocal...")
        if SessionLocal is None:
            print("❌ SessionLocal is None")
            return False
        else:
            print("✅ SessionLocal is available")
        
        # Test 4: Test database connection
        print("\n4. Testing database connection...")
        with SessionLocal() as session:
            result = session.execute("SELECT 1").fetchone()
            print(f"✅ Database connection OK: {result}")
        
        # Test 5: Test symbol processing
        print("\n5. Testing symbol processing...")
        symbol_config = {
            'symbol': 'AAPL',
            'bubefsm2': 0.85,
            'bubefsm5': 0.85,
            'bubefsm15': 0.85,
            'bubefsm30': 0.85,
            'bubefs_1h': 0.85
        }
        
        result = _process_symbol_macd_multi(
            symbol_id=1,
            symbol='AAPL',
            exchange='NASDAQ',
            symbol_config=symbol_config,
            fast_period=7,
            slow_period=113,
            signal_period=144
        )
        
        print(f"✅ Symbol processing result: {result}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print(f"📋 Traceback:")
        traceback.print_exc()
        return False
    
    print(f"\n🎉 All tests passed!")
    return True

if __name__ == '__main__':
    success = debug_macd_error()
    sys.exit(0 if success else 1)
