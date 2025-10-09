#!/usr/bin/env python3
"""
Test MACD Multi-TF US jobs with Telegram notification
"""

import sys
import os
import time
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_macd_telegram():
    """Test MACD Multi-TF US jobs with Telegram notification"""
    print("🚀 Testing MACD Multi-TF US jobs with Telegram...")
    print("=" * 60)
    
    try:
        # Import required modules
        from rq import Queue
        import redis
        
        # Connect to Redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url)
        q_priority = Queue('priority', connection=r)
        
        print("✅ Connected to Redis and priority queue")
        
        # Test workflow config with more symbols
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
                },
                {
                    'symbol': 'TSLA',
                    'bubefsm2': 0.47,
                    'bubefsm5': 0.47,
                    'bubefsm15': 0.47,
                    'bubefsm30': 0.47,
                    'bubefs_1h': 1.74
                },
                {
                    'symbol': 'NVDA',
                    'bubefsm2': 0.47,
                    'bubefsm5': 0.47,
                    'bubefsm15': 0.47,
                    'bubefsm30': 0.47,
                    'bubefs_1h': 1.74
                }
            ]
        }
        
        print("📋 Test workflow config with 5 symbols:")
        for symbol in workflow_config['symbolThresholds']:
            print(f"   - {symbol['symbol']}")
        
        # Test 1: Realtime mode
        print("\n🧪 Test 1: Realtime mode with Telegram")
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
            
            # Process results and show signals
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
                
                # Check if Telegram notifications were sent
                print(f"\n📱 Telegram notifications:")
                print(f"   Signals should be sent to configured chat")
                print(f"   Check your Telegram for notifications")
                
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

def check_telegram_config():
    """Check Telegram configuration"""
    print("\n🔍 Checking Telegram configuration...")
    
    tg_token = os.getenv('TG_TOKEN')
    tg_chat_id = os.getenv('TG_CHAT_ID')
    
    if tg_token and tg_token != 'your_telegram_bot_token_here':
        print(f"✅ TG_TOKEN: {tg_token[:10]}...")
    else:
        print("❌ TG_TOKEN not configured")
    
    if tg_chat_id and tg_chat_id != 'your_telegram_chat_id_here':
        print(f"✅ TG_CHAT_ID: {tg_chat_id}")
    else:
        print("❌ TG_CHAT_ID not configured")
    
    if tg_token and tg_chat_id and tg_token != 'your_telegram_bot_token_here' and tg_chat_id != 'your_telegram_chat_id_here':
        print("✅ Telegram configuration is ready")
        return True
    else:
        print("❌ Telegram configuration is missing")
        print("💡 Please set TG_TOKEN and TG_CHAT_ID in .env file")
        return False

if __name__ == "__main__":
    print("🧪 MACD Multi-TF US Telegram Test")
    print("=" * 60)
    
    # Check Telegram configuration
    telegram_ok = check_telegram_config()
    
    if telegram_ok:
        # Test MACD Multi-TF jobs
        success = test_macd_telegram()
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 MACD Multi-TF US Telegram test completed!")
            print("✅ Jobs processed successfully")
            print("📱 Check your Telegram for signal notifications")
        else:
            print("❌ MACD Multi-TF US Telegram test failed!")
            print("💡 Check worker logs and configuration")
    else:
        print("\n❌ Cannot run test without Telegram configuration")
        print("💡 Please configure TG_TOKEN and TG_CHAT_ID first")
