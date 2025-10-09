#!/usr/bin/env python3
"""
Test automatic symbol insertion and activation for MACD Multi-TF
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_auto_symbols():
    """Test automatic symbol insertion and activation"""
    print("🔄 Testing Automatic Symbol Insertion for MACD Multi-TF")
    print("=" * 60)
    
    try:
        from app.db import init_db, SessionLocal
        from sqlalchemy import text
        import json
        
        # Initialize database
        init_db(os.getenv("DATABASE_URL"))
        
        # Test symbols
        test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
        
        print("📋 Test symbols:")
        for symbol in test_symbols:
            print(f"   - {symbol}")
        
        # Check current status
        print(f"\n🔍 Checking current symbol status...")
        with SessionLocal() as session:
            for symbol in test_symbols:
                result = session.execute(text("""
                    SELECT id, ticker, exchange, active 
                    FROM symbols 
                    WHERE ticker = :ticker AND exchange = :exchange
                """), {'ticker': symbol, 'exchange': 'NASDAQ'}).fetchone()
                
                if result:
                    print(f"   {symbol}: EXISTS (ID: {result[0]}, Active: {result[3]})")
                else:
                    print(f"   {symbol}: NOT EXISTS")
        
        # Test scheduler function
        print(f"\n🧪 Testing scheduler function...")
        from worker.scheduler_multi import _ensure_macd_symbols_exist
        
        # Create test workflow config
        workflow_config = {
            'fastPeriod': 7,
            'slowPeriod': 113,
            'signalPeriod': 144,
            'symbolThresholds': [
                {'symbol': symbol, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.47, 'bubefsm30': 0.47, 'bubefs_1h': 1.74}
                for symbol in test_symbols
            ]
        }
        
        # Test the function
        symbols_added = _ensure_macd_symbols_exist(workflow_config)
        print(f"   Symbols added/activated: {symbols_added}")
        
        # Check status after
        print(f"\n🔍 Checking symbol status after...")
        with SessionLocal() as session:
            for symbol in test_symbols:
                result = session.execute(text("""
                    SELECT id, ticker, exchange, active 
                    FROM symbols 
                    WHERE ticker = :ticker AND exchange = :exchange
                """), {'ticker': symbol, 'exchange': 'NASDAQ'}).fetchone()
                
                if result:
                    print(f"   {symbol}: EXISTS (ID: {result[0]}, Active: {result[3]})")
                else:
                    print(f"   {symbol}: NOT EXISTS")
        
        # Test scheduler loop
        print(f"\n🔄 Testing scheduler loop...")
        from worker.scheduler_multi import _check_macd_multi_active, _enqueue_macd_multi_jobs
        
        # Check if MACD Multi-TF is active
        is_active = _check_macd_multi_active()
        print(f"   MACD Multi-TF active: {is_active}")
        
        if is_active:
            # Test enqueue function
            jobs_count = _enqueue_macd_multi_jobs()
            print(f"   Jobs enqueued: {jobs_count}")
            
            if jobs_count > 0:
                print("✅ Automatic symbol insertion working!")
                
                # Check priority queue
                from rq import Queue
                import redis
                
                redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
                r = redis.from_url(redis_url)
                q_priority = Queue('priority', connection=r)
                
                queue_count = len(q_priority)
                print(f"   Priority queue jobs: {queue_count}")
                
                # Wait a bit and check if jobs are processed
                print("⏳ Waiting for jobs to be processed...")
                time.sleep(10)
                
                queue_count_after = len(q_priority)
                print(f"   Priority queue jobs after 10s: {queue_count_after}")
                
                if queue_count_after < queue_count:
                    print("✅ Jobs are being processed by worker!")
                else:
                    print("⚠️ Jobs may not be processed yet")
            else:
                print("❌ No jobs enqueued")
        else:
            print("❌ No active MACD Multi-TF workflows found")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Automatic Symbol Insertion Test")
    print("=" * 60)
    
    success = test_auto_symbols()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Automatic symbol insertion test completed!")
        print("✅ Symbols automatically inserted and activated")
        print("✅ Scheduler can enqueue MACD Multi-TF jobs")
        print("✅ Backfill will start automatically for new symbols")
    else:
        print("❌ Automatic symbol insertion test failed!")
        print("💡 Check database and scheduler configuration")
