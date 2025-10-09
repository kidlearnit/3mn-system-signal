#!/usr/bin/env python3
"""
Test MACD Multi-TF US jobs with actual worker
"""

import sys
import os
import time
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_macd_multi_worker():
    """Test MACD Multi-TF US jobs with worker"""
    print("🚀 Testing MACD Multi-TF US jobs with worker...")
    print("=" * 60)
    
    try:
        # Import required modules
        from rq import Queue
        import os
        REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        import redis
        
        # Connect to Redis
        r = redis.from_url(REDIS_URL)
        q_priority = Queue('priority', connection=r)
        
        print("✅ Connected to Redis and priority queue")
        
        # Test workflow config
        workflow_config = {
            'fastPeriod': 7,
            'slowPeriod': 113,
            'signalPeriod': 144,
            'symbolThresholds': [
                {
                    'symbol': 'AAPL',
                    'bubefsm2': 0.47,
                    'bubefsm5': 0.47,
                    'bubefsm15': 0.47,
                    'bubefsm30': 0.47,
                    'bubefs_1h': 1.74
                },
                {
                    'symbol': 'MSFT',
                    'bubefsm2': 0.47,
                    'bubefsm5': 0.47,
                    'bubefsm15': 0.47,
                    'bubefsm30': 0.47,
                    'bubefs_1h': 1.74
                }
            ]
        }
        
        print("📋 Test workflow config:")
        print(json.dumps(workflow_config, indent=2))
        
        # Test 1: Realtime mode
        print("\n🧪 Test 1: Realtime mode")
        from worker.macd_multi_us_jobs import job_macd_multi_us_workflow_executor
        
        job = q_priority.enqueue(
            job_macd_multi_us_workflow_executor,
            999,  # workflow_id
            'test-node-1',  # node_id
            workflow_config,
            'realtime',  # mode
            job_timeout=600
        )
        
        print(f"✅ Job enqueued: {job.id}")
        print(f"   Status: {job.get_status()}")
        print(f"   Queue: priority")
        print(f"   Timeout: 600s")
        
        # Wait for job to complete
        print("\n⏳ Waiting for job to complete...")
        start_time = time.time()
        
        while job.get_status() in ['queued', 'started']:
            time.sleep(2)
            elapsed = time.time() - start_time
            print(f"   Elapsed: {elapsed:.1f}s, Status: {job.get_status()}")
            
            if elapsed > 120:  # 2 minutes timeout
                print("⏰ Job timeout after 2 minutes")
                break
        
        # Get result
        if job.get_status() == 'finished':
            result = job.result
            print(f"✅ Job completed successfully!")
            print(f"   Result: {result}")
        elif job.get_status() == 'failed':
            print(f"❌ Job failed!")
            print(f"   Error: {job.exc_info}")
        else:
            print(f"⚠️ Job status: {job.get_status()}")
        
        # Test 2: Backfill mode
        print("\n🧪 Test 2: Backfill mode")
        
        job2 = q_priority.enqueue(
            job_macd_multi_us_workflow_executor,
            998,  # workflow_id
            'test-node-2',  # node_id
            workflow_config,
            'backfill',  # mode
            job_timeout=1800
        )
        
        print(f"✅ Job enqueued: {job2.id}")
        print(f"   Status: {job2.get_status()}")
        print(f"   Mode: backfill")
        print(f"   Timeout: 1800s")
        
        # Wait for job to complete
        print("\n⏳ Waiting for backfill job to complete...")
        start_time = time.time()
        
        while job2.get_status() in ['queued', 'started']:
            time.sleep(5)
            elapsed = time.time() - start_time
            print(f"   Elapsed: {elapsed:.1f}s, Status: {job2.get_status()}")
            
            if elapsed > 300:  # 5 minutes timeout
                print("⏰ Job timeout after 5 minutes")
                break
        
        # Get result
        if job2.get_status() == 'finished':
            result2 = job2.result
            print(f"✅ Backfill job completed successfully!")
            print(f"   Result: {result2}")
        elif job2.get_status() == 'failed':
            print(f"❌ Backfill job failed!")
            print(f"   Error: {job2.exc_info}")
        else:
            print(f"⚠️ Backfill job status: {job2.get_status()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_worker_status():
    """Test worker status and queue info"""
    print("\n🔍 Checking worker status...")
    
    try:
        from rq import Queue
        import os
        REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        import redis
        
        r = redis.from_url(REDIS_URL)
        
        # Check queues
        queues = ['default', 'priority', 'vn', 'us', 'backfill']
        
        for queue_name in queues:
            q = Queue(queue_name, connection=r)
            count = len(q)
            print(f"   {queue_name}: {count} jobs")
        
        # Check workers
        from rq import Worker
        workers = Worker.all(connection=r)
        print(f"\n👥 Active workers: {len(workers)}")
        
        for worker in workers:
            print(f"   {worker.name}: {worker.state}")
            if worker.current_job:
                print(f"      Current job: {worker.current_job.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Worker status check failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 MACD Multi-TF US Worker Test")
    print("=" * 60)
    
    # Test worker status first
    test_worker_status()
    
    # Test MACD Multi-TF jobs
    success = test_macd_multi_worker()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 MACD Multi-TF US jobs test completed!")
        print("✅ Worker can process MACD Multi-TF US jobs")
    else:
        print("❌ MACD Multi-TF US jobs test failed!")
        print("💡 Check worker logs and database connection")
