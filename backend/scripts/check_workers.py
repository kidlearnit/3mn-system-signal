#!/usr/bin/env python3
"""
Check and compare workers in Docker
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_workers():
    """Check all workers and their configurations"""
    print("🔍 Checking Workers in Docker")
    print("=" * 50)
    
    try:
        from rq import Queue, Worker
        import redis
        
        # Connect to Redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url)
        
        print("✅ Connected to Redis")
        
        # Check all workers
        workers = Worker.all(connection=r)
        print(f"\n👥 Active Workers: {len(workers)}")
        
        for worker in workers:
            print(f"\n📋 Worker: {worker.name}")
            print(f"   State: {worker.state}")
            print(f"   Queues: {worker.queue_names()}")
            print(f"   Current Job: {worker.current_job_id if hasattr(worker, 'current_job_id') else 'None'}")
        
        # Check queues
        print(f"\n📊 Queue Status:")
        queues = ['default', 'priority', 'vn', 'us', 'backfill']
        
        for queue_name in queues:
            q = Queue(queue_name, connection=r)
            count = len(q)
            print(f"   {queue_name}: {count} jobs")
        
        # Check if MACD Multi-TF jobs are in priority queue
        q_priority = Queue('priority', connection=r)
        jobs = q_priority.jobs
        
        print(f"\n🔍 Priority Queue Jobs:")
        if jobs:
            for job in jobs:
                print(f"   Job ID: {job.id}")
                print(f"   Function: {job.func_name}")
                print(f"   Args: {job.args}")
                print(f"   Status: {job.get_status()}")
                print()
        else:
            print("   No jobs in priority queue")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_workers():
    """Compare worker configurations"""
    print("\n🔍 Comparing Worker Configurations")
    print("=" * 50)
    
    print("📋 Worker Services in Docker Compose:")
    print("   1. worker: Listens to ['default', 'priority'] queues")
    print("   2. worker_us: Listens to ['us'] queue")
    print("   3. worker_vn: Listens to ['vn'] queue")
    print("   4. worker_backfill: Listens to ['backfill'] queue")
    
    print("\n📊 MACD Multi-TF US Jobs:")
    print("   - Job Name: job_macd_multi_us_workflow_executor")
    print("   - Queue: priority")
    print("   - Worker: worker (main worker)")
    print("   - Function: worker.macd_multi_us_jobs.job_macd_multi_us_workflow_executor")
    
    print("\n🔄 Worker US vs MACD Multi-TF:")
    print("   - worker_us: Handles regular US market jobs")
    print("   - MACD Multi-TF: Handled by main worker (priority queue)")
    print("   - Conflict Prevention: Scheduler checks for active MACD Multi-TF workflows")
    print("   - When MACD Multi-TF active: worker_us is paused")

if __name__ == "__main__":
    print("🧪 Worker Analysis")
    print("=" * 50)
    
    # Check workers
    workers_ok = check_workers()
    
    # Compare configurations
    compare_workers()
    
    print("\n" + "=" * 50)
    if workers_ok:
        print("✅ Worker analysis completed!")
    else:
        print("❌ Worker analysis failed!")
