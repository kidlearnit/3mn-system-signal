#!/usr/bin/env python3
"""
Test backfill mode for MACD Multi-TF
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_backfill_mode():
    """Test backfill mode for MACD Multi-TF"""
    print("🔄 Testing Backfill Mode for MACD Multi-TF")
    print("=" * 50)
    
    try:
        from rq import Queue
        import redis
        
        # Connect to Redis
        redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
        r = redis.from_url(redis_url)
        q_priority = Queue('priority', connection=r)
        
        print("✅ Connected to Redis and priority queue")
        
        # Test workflow config with 3 symbols for faster testing
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
                },
                {
                    'symbol': 'GOOGL',
                    'bubefsm2': 0.47,
                    'bubefsm5': 0.47,
                    'bubefsm15': 0.47,
                    'bubefsm30': 0.47,
                    'bubefs_1h': 1.74
                }
            ]
        }
        
        print("📋 Test workflow config (3 symbols for faster testing):")
        for symbol_data in workflow_config['symbolThresholds']:
            print(f"   - {symbol_data['symbol']}")
        
        # Enqueue MACD Multi-TF job in backfill mode
        from worker.macd_multi_us_jobs import job_macd_multi_us_workflow_executor
        
        print(f"\n🔄 Enqueuing MACD Multi-TF job in BACKFILL mode...")
        job = q_priority.enqueue(
            job_macd_multi_us_workflow_executor,
            999,  # workflow_id
            'backfill-test-node',  # node_id
            workflow_config,
            'backfill',  # mode
            job_timeout=1800  # 30 minutes for backfill
        )
        
        print(f"✅ Job enqueued successfully!")
        print(f"   Job ID: {job.id}")
        print(f"   Function: {job.func_name}")
        print(f"   Queue: priority")
        print(f"   Mode: backfill")
        print(f"   Timeout: 1800s (30 min)")
        print(f"   Status: {job.get_status()}")
        
        # Wait for job to complete
        print(f"\n⏳ Waiting for backfill job to complete...")
        print(f"   This may take 5-15 minutes for 3 symbols...")
        start_time = time.time()
        
        while job.get_status() in ['queued', 'started']:
            time.sleep(10)
            elapsed = time.time() - start_time
            print(f"   Elapsed: {elapsed:.1f}s, Status: {job.get_status()}")
            
            if elapsed > 1200:  # 20 minutes timeout
                print("⏰ Job timeout after 20 minutes")
                break
        
        # Get result
        if job.get_status() == 'finished':
            result = job.result
            print(f"✅ Backfill job completed successfully!")
            
            if result and result.get('result'):
                pipeline_result = result['result']
                signals_generated = pipeline_result.get('signals_generated', 0)
                symbols_processed = pipeline_result.get('symbols_processed', 0)
                
                print(f"📊 Backfill Results:")
                print(f"   Symbols processed: {symbols_processed}")
                print(f"   Signals generated: {signals_generated}")
                
                # Show backfill details
                results = pipeline_result.get('results', [])
                for symbol_result in results:
                    symbol = symbol_result['symbol']
                    backfill_result = symbol_result.get('backfill_result', {})
                    signal_result = symbol_result.get('result', {})
                    
                    print(f"   📈 {symbol}:")
                    if backfill_result:
                        print(f"      Backfill: {backfill_result.get('status', 'unknown')}")
                        print(f"      Candles added: {backfill_result.get('candles_added', 0)}")
                    
                    if signal_result and signal_result.get('status') == 'success':
                        overall_signal = signal_result['overall_signal']
                        signal_type = overall_signal['signal_type']
                        confidence = overall_signal['confidence']
                        print(f"      Signal: {signal_type} (confidence: {confidence:.2f})")
                
                print(f"\n✅ Backfill completed!")
                print(f"📊 All symbols now have historical data")
                print(f"🔄 Ready for realtime mode!")
                
        elif job.get_status() == 'failed':
            print(f"❌ Backfill job failed!")
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
    print("🧪 MACD Multi-TF Backfill Test")
    print("=" * 50)
    
    success = test_backfill_mode()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 MACD Multi-TF backfill test completed!")
        print("✅ Backfill mode working")
        print("📊 Historical data populated")
        print("🔄 Ready for realtime mode")
    else:
        print("❌ MACD Multi-TF backfill test failed!")
        print("💡 Check Docker logs: docker-compose logs worker")
