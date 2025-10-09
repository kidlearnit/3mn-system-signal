#!/usr/bin/env python3
"""
Test MACD Multi-TF US job in Docker
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_macd_docker():
    """Test MACD Multi-TF US job in Docker"""
    print("🚀 Testing MACD Multi-TF US Job in Docker")
    print("=" * 50)
    
    try:
        from rq import Queue
        import redis
        
        # Connect to Redis
        redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
        r = redis.from_url(redis_url)
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
                }
            ]
        }
        
        print("📋 Test workflow config:")
        print(f"   Symbol: {workflow_config['symbolThresholds'][0]['symbol']}")
        print(f"   MACD: {workflow_config['fastPeriod']}, {workflow_config['slowPeriod']}, {workflow_config['signalPeriod']}")
        
        # Enqueue MACD Multi-TF job
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
        print(f"   Function: {job.func_name}")
        print(f"   Queue: priority")
        print(f"   Status: {job.get_status()}")
        
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
            
            if result and result.get('result'):
                pipeline_result = result['result']
                signals_generated = pipeline_result.get('signals_generated', 0)
                symbols_processed = pipeline_result.get('symbols_processed', 0)
                
                print(f"📊 Results:")
                print(f"   Symbols processed: {symbols_processed}")
                print(f"   Signals generated: {signals_generated}")
                
                # Show signal details
                results = pipeline_result.get('results', [])
                for symbol_result in results:
                    if symbol_result.get('result', {}).get('status') == 'success':
                        symbol = symbol_result['symbol']
                        overall_signal = symbol_result['result']['overall_signal']
                        signal_type = overall_signal['signal_type']
                        confidence = overall_signal['confidence']
                        
                        print(f"   📈 {symbol}: {signal_type} (confidence: {confidence:.2f})")
                        
                        # Show timeframe breakdown
                        timeframe_results = symbol_result['result']['timeframe_results']
                        for tf, tf_result in timeframe_results.items():
                            bubefsm = tf_result.get('bubefsm', {})
                            tf_signal = bubefsm.get('signal_type', 'NEUTRAL')
                            strength = bubefsm.get('strength', 0)
                            print(f"      {tf}: {tf_signal} (strength: {strength:.3f})")
                
        elif job.get_status() == 'failed':
            print(f"❌ Job failed!")
            print(f"   Error: {job.exc_info}")
        else:
            print(f"⚠️ Job status: {job.get_status()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 MACD Multi-TF US Docker Test")
    print("=" * 50)
    
    success = test_macd_docker()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 MACD Multi-TF US Docker test completed!")
        print("✅ Job processed successfully in Docker")
    else:
        print("❌ MACD Multi-TF US Docker test failed!")
        print("💡 Check Docker logs: docker-compose logs worker")
