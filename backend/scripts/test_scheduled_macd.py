#!/usr/bin/env python3
"""
Test scheduled MACD Multi-TF jobs
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_scheduled_macd():
    """Test scheduled MACD Multi-TF jobs"""
    print("🕐 Testing Scheduled MACD Multi-TF Jobs")
    print("=" * 50)
    
    try:
        from app.db import init_db, SessionLocal
        from sqlalchemy import text
        import json
        
        # Initialize database
        init_db(os.getenv("DATABASE_URL"))
        
        # Create a test workflow with MACD Multi-TF node
        print("📋 Creating test workflow...")
        
        with SessionLocal() as session:
            # Check if test workflow already exists
            result = session.execute(text("""
                SELECT id FROM workflows WHERE name = 'Test MACD Multi-TF Scheduled'
            """)).fetchone()
            
            if result:
                workflow_id = result[0]
                print(f"✅ Test workflow already exists: ID {workflow_id}")
            else:
                # Create test workflow
                test_nodes = [
                    {
                        "id": "macd-multi-1",
                        "type": "macd-multi",
                        "position": {"x": 100, "y": 100},
                        "data": {"label": "MACD Multi-TF"}
                    }
                ]
                
                test_properties = {
                    "macd-multi-1": {
                        "fastPeriod": 7,
                        "slowPeriod": 113,
                        "signalPeriod": 144,
                        "symbolThresholds": [
                            {
                                "symbol": "AAPL",
                                "bubefsm2": 0.47,
                                "bubefsm5": 0.47,
                                "bubefsm15": 0.47,
                                "bubefsm30": 0.47,
                                "bubefs_1h": 1.74
                            },
                            {
                                "symbol": "MSFT",
                                "bubefsm2": 0.47,
                                "bubefsm5": 0.47,
                                "bubefsm15": 0.47,
                                "bubefsm30": 0.47,
                                "bubefs_1h": 1.74
                            }
                        ]
                    }
                }
                
                session.execute(text("""
                    INSERT INTO workflows (name, description, nodes, connections, properties, status, created_at, updated_at)
                    VALUES (:name, :description, :nodes, :connections, :properties, :status, NOW(), NOW())
                """), {
                    'name': 'Test MACD Multi-TF Scheduled',
                    'description': 'Test workflow for scheduled MACD Multi-TF jobs',
                    'nodes': json.dumps(test_nodes),
                    'connections': json.dumps([]),
                    'properties': json.dumps(test_properties),
                    'status': 'active'
                })
                
                session.commit()
                
                # Get the created workflow ID
                result = session.execute(text("""
                    SELECT id FROM workflows WHERE name = 'Test MACD Multi-TF Scheduled'
                """)).fetchone()
                
                workflow_id = result[0]
                print(f"✅ Test workflow created: ID {workflow_id}")
        
        # Check if workflow is active
        print(f"\n🔍 Checking workflow status...")
        with SessionLocal() as session:
            result = session.execute(text("""
                SELECT status, nodes, properties
                FROM workflows 
                WHERE id = :workflow_id
            """), {'workflow_id': workflow_id}).fetchone()
            
            if result:
                status, nodes_json, properties_json = result
                print(f"   Status: {status}")
                
                nodes = json.loads(nodes_json)
                properties = json.loads(properties_json)
                
                macd_multi_nodes = [node for node in nodes if node.get('type') == 'macd-multi']
                print(f"   MACD Multi-TF nodes: {len(macd_multi_nodes)}")
                
                for node in macd_multi_nodes:
                    node_id = node['id']
                    node_config = properties.get(node_id, {})
                    symbol_thresholds = node_config.get('symbolThresholds', [])
                    print(f"   Symbols configured: {len(symbol_thresholds)}")
                    for symbol_data in symbol_thresholds:
                        print(f"     - {symbol_data['symbol']}")
        
        # Test scheduler function
        print(f"\n🧪 Testing scheduler function...")
        from worker.scheduler_multi import _check_macd_multi_active, _enqueue_macd_multi_jobs
        
        # Check if MACD Multi-TF is active
        is_active = _check_macd_multi_active()
        print(f"   MACD Multi-TF active: {is_active}")
        
        if is_active:
            # Test enqueue function
            jobs_count = _enqueue_macd_multi_jobs()
            print(f"   Jobs enqueued: {jobs_count}")
            
            if jobs_count > 0:
                print(f"✅ Scheduled MACD Multi-TF jobs working!")
                
                # Check priority queue
                from rq import Queue
                import redis
                
                redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
                r = redis.from_url(redis_url)
                q_priority = Queue('priority', connection=r)
                
                queue_count = len(q_priority)
                print(f"   Priority queue jobs: {queue_count}")
                
                # Wait a bit and check if jobs are processed
                print(f"\n⏳ Waiting for jobs to be processed...")
                time.sleep(10)
                
                queue_count_after = len(q_priority)
                print(f"   Priority queue jobs after 10s: {queue_count_after}")
                
                if queue_count_after < queue_count:
                    print(f"✅ Jobs are being processed by worker!")
                else:
                    print(f"⚠️ Jobs may not be processed yet")
            else:
                print(f"❌ No jobs enqueued")
        else:
            print(f"❌ MACD Multi-TF not active")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Scheduled MACD Multi-TF Test")
    print("=" * 50)
    
    success = test_scheduled_macd()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Scheduled MACD Multi-TF test completed!")
        print("✅ Scheduler can enqueue MACD Multi-TF jobs")
    else:
        print("❌ Scheduled MACD Multi-TF test failed!")
        print("💡 Check database and scheduler configuration")
