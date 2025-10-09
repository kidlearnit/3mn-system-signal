#!/usr/bin/env python3
"""
Simple test for scheduled MACD Multi-TF jobs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def simple_scheduled_test():
    """Simple test for scheduled MACD Multi-TF jobs"""
    print("🕐 Simple Scheduled MACD Multi-TF Test")
    print("=" * 50)
    
    try:
        # Test scheduler functions
        print("🧪 Testing scheduler functions...")
        
        # Import scheduler functions
        from worker.scheduler_multi import _check_macd_multi_active, _enqueue_macd_multi_jobs
        
        # Check if MACD Multi-TF is active
        print("🔍 Checking if MACD Multi-TF workflows are active...")
        is_active = _check_macd_multi_active()
        print(f"   MACD Multi-TF active: {is_active}")
        
        if is_active:
            print("✅ MACD Multi-TF workflows are active!")
            
            # Test enqueue function
            print("🚀 Testing enqueue function...")
            jobs_count = _enqueue_macd_multi_jobs()
            print(f"   Jobs enqueued: {jobs_count}")
            
            if jobs_count > 0:
                print("✅ Scheduled MACD Multi-TF jobs working!")
                
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
        else:
            print("❌ No active MACD Multi-TF workflows found")
            print("💡 Create a workflow with MACD Multi-TF node and set status to 'active'")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Simple Scheduled MACD Multi-TF Test")
    print("=" * 50)
    
    success = simple_scheduled_test()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Simple scheduled MACD Multi-TF test completed!")
    else:
        print("❌ Simple scheduled MACD Multi-TF test failed!")
