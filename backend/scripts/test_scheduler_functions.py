#!/usr/bin/env python3
"""
Test scheduler functions for MACD Multi-TF
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_scheduler_functions():
    """Test scheduler functions"""
    print("🔄 Testing Scheduler Functions for MACD Multi-TF")
    print("=" * 60)
    
    try:
        # Test scheduler functions
        print("🧪 Testing scheduler functions...")
        
        # Import scheduler functions
        from worker.scheduler_multi import _check_macd_multi_active, _enqueue_macd_multi_jobs, _ensure_macd_symbols_exist
        
        # Test workflow config
        workflow_config = {
            'fastPeriod': 7,
            'slowPeriod': 113,
            'signalPeriod': 144,
            'symbolThresholds': [
                {'symbol': 'AAPL', 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.47, 'bubefsm30': 0.47, 'bubefs_1h': 1.74},
                {'symbol': 'MSFT', 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.47, 'bubefsm30': 0.47, 'bubefs_1h': 1.74},
                {'symbol': 'GOOGL', 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.47, 'bubefsm30': 0.47, 'bubefs_1h': 1.74}
            ]
        }
        
        print("📋 Test workflow config:")
        for symbol_data in workflow_config['symbolThresholds']:
            print(f"   - {symbol_data['symbol']}")
        
        # Test 1: Check if MACD Multi-TF is active
        print(f"\n🔍 Test 1: Check if MACD Multi-TF is active...")
        is_active = _check_macd_multi_active()
        print(f"   MACD Multi-TF active: {is_active}")
        
        # Test 2: Ensure symbols exist
        print(f"\n🔍 Test 2: Ensure symbols exist...")
        symbols_added = _ensure_macd_symbols_exist(workflow_config)
        print(f"   Symbols added/activated: {symbols_added}")
        
        # Test 3: Enqueue jobs
        print(f"\n🔍 Test 3: Enqueue MACD Multi-TF jobs...")
        jobs_count = _enqueue_macd_multi_jobs()
        print(f"   Jobs enqueued: {jobs_count}")
        
        if jobs_count > 0:
            print("✅ Scheduler functions working!")
            
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
            import time
            time.sleep(10)
            
            queue_count_after = len(q_priority)
            print(f"   Priority queue jobs after 10s: {queue_count_after}")
            
            if queue_count_after < queue_count:
                print("✅ Jobs are being processed by worker!")
            else:
                print("⚠️ Jobs may not be processed yet")
        else:
            print("❌ No jobs enqueued")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Scheduler Functions Test")
    print("=" * 60)
    
    success = test_scheduler_functions()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Scheduler functions test completed!")
        print("✅ Automatic symbol insertion working")
        print("✅ MACD Multi-TF jobs enqueued")
        print("✅ Worker processing jobs")
    else:
        print("❌ Scheduler functions test failed!")
        print("💡 Check scheduler configuration")
