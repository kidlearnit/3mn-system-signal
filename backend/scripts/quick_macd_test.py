#!/usr/bin/env python3
"""
Quick MACD Multi-TF US test with Telegram
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def quick_test():
    """Quick test MACD Multi-TF US with Telegram"""
    print("🚀 Quick MACD Multi-TF US Test with Telegram")
    print("=" * 50)
    
    # Check Telegram config
    tg_token = os.getenv('TG_TOKEN')
    tg_chat_id = os.getenv('TG_CHAT_ID')
    
    if not tg_token or not tg_chat_id or tg_token == 'your_telegram_bot_token_here':
        print("❌ Telegram not configured!")
        print("💡 Please set TG_TOKEN and TG_CHAT_ID in .env file")
        return False
    
    print(f"✅ Telegram configured: {tg_token[:10]}...")
    
    try:
        # Import and run MACD Multi-TF
        from worker.macd_multi_us_jobs import job_macd_multi_us_pipeline
        
        # Simple config
        config = {
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
        
        print("🧪 Running MACD Multi-TF US pipeline...")
        result = job_macd_multi_us_pipeline(config, mode='realtime')
        
        print(f"✅ Pipeline completed!")
        print(f"📊 Symbols processed: {result.get('symbols_processed', 0)}")
        print(f"📈 Signals generated: {result.get('signals_generated', 0)}")
        
        # Show results
        results = result.get('results', [])
        for symbol_result in results:
            if symbol_result.get('result', {}).get('status') == 'success':
                symbol = symbol_result['symbol']
                overall_signal = symbol_result['result']['overall_signal']
                signal_type = overall_signal['signal_type']
                confidence = overall_signal['confidence']
                
                print(f"📈 {symbol}: {signal_type} (confidence: {confidence:.2f})")
        
        print("📱 Check your Telegram for notifications!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_test()
    
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n❌ Test failed!")
