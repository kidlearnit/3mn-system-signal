#!/usr/bin/env python3
"""
Step by step test để tìm lỗi
"""

import os
import sys
import traceback

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def step_by_step_test():
    """Step by step test"""
    
    print("🔍 STEP BY STEP TEST")
    print("=" * 40)
    
    try:
        # Step 1: Test database
        print("Step 1: Testing database...")
        from app.db import SessionLocal, init_db
        init_db(os.getenv("DATABASE_URL"))
        
        if SessionLocal is None:
            print("❌ SessionLocal is None")
            return False
        
        with SessionLocal() as session:
            result = session.execute("SELECT 1").fetchone()
            print(f"✅ Database OK: {result}")
        
        # Step 2: Test symbol lookup
        print("\nStep 2: Testing symbol lookup...")
        from sqlalchemy import text
        
        with SessionLocal() as session:
            result = session.execute(text("""
                SELECT id FROM symbols 
                WHERE ticker = :ticker AND exchange = :exchange
            """), {'ticker': 'AAPL', 'exchange': 'NASDAQ'}).fetchone()
            
            if result:
                symbol_id = result[0]
                print(f"✅ Symbol found: AAPL (ID: {symbol_id})")
            else:
                print("❌ Symbol AAPL not found")
                return False
        
        # Step 3: Test data loading
        print("\nStep 3: Testing data loading...")
        from app.services.candle_utils import load_candles_1m_df
        
        df = load_candles_1m_df(symbol_id)
        print(f"✅ Data loaded: {len(df)} rows")
        
        if df.empty:
            print("⚠️  No data available")
            return False
        
        # Step 4: Test MACD calculation
        print("\nStep 4: Testing MACD calculation...")
        from app.services.resample import resample_ohlcv
        from app.services.indicators import compute_macd
        
        # Resample to 2m
        df_2m = resample_ohlcv(df, '2m')
        print(f"✅ Resampled to 2m: {len(df_2m)} rows")
        
        # Calculate MACD
        macd_result = compute_macd(df_2m, 7, 113, 144)
        print(f"✅ MACD calculated: {len(macd_result)} rows")
        
        # Step 5: Test BuBeFSM logic
        print("\nStep 5: Testing BuBeFSM logic...")
        from worker.macd_multi_us_jobs import _calculate_bubefsm_signals
        
        if len(macd_result) > 0:
            latest = macd_result.iloc[-1]
            result = _calculate_bubefsm_signals(
                latest['macd'], latest['signal'], 0.85
            )
            print(f"✅ BuBeFSM result: {result}")
        else:
            print("❌ No MACD data for BuBeFSM test")
            return False
        
        print(f"\n🎉 ALL STEPS PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ ERROR at step: {e}")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = step_by_step_test()
    sys.exit(0 if success else 1)
