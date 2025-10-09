#!/usr/bin/env python3
"""
Monitor scheduled MACD Multi-TF jobs
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def monitor_scheduled_macd():
    """Monitor scheduled MACD Multi-TF jobs"""
    print("🕐 Monitoring Scheduled MACD Multi-TF Jobs")
    print("=" * 50)
    
    try:
        from rq import Queue
        import redis
        
        # Connect to Redis
        redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
        r = redis.from_url(redis_url)
        q_priority = Queue('priority', connection=r)
        
        print("✅ Connected to Redis and priority queue")
        
        # Monitor for 2 minutes
        print("⏳ Monitoring for 2 minutes...")
        start_time = time.time()
        
        while time.time() - start_time < 120:  # 2 minutes
            # Check queue status
            queue_count = len(q_priority)
            
            # Check if there are any jobs
            if queue_count > 0:
                print(f"📊 Priority queue: {queue_count} jobs")
                
                # Show job details
                jobs = q_priority.jobs
                for job in jobs:
                    print(f"   - Job ID: {job.id}")
                    print(f"     Function: {job.func_name}")
                    print(f"     Status: {job.get_status()}")
                    print(f"     Created: {job.created_at}")
            else:
                print("📊 Priority queue: 0 jobs")
            
            # Wait 30 seconds
            time.sleep(30)
        
        print("✅ Monitoring completed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Monitoring failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Scheduled MACD Multi-TF Monitor")
    print("=" * 50)
    
    success = monitor_scheduled_macd()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Monitoring completed!")
    else:
        print("❌ Monitoring failed!")
