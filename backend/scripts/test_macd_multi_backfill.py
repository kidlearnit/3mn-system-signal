#!/usr/bin/env python3
"""
Test script for MACD Multi-TF US backfill functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from worker.macd_multi_us_jobs import job_macd_multi_us_pipeline

def test_backfill_mode():
    """Test MACD Multi-TF US backfill mode"""
    
    # Sample workflow configuration with 3 symbols for testing
    workflow_config = {
        'fastPeriod': 7,
        'slowPeriod': 113,
        'signalPeriod': 144,
        'symbolThresholds': [
            {
                'symbol': 'NVDA',
                'bubefsm2': 0.47,
                'bubefsm5': 0.47,
                'bubefsm15': 0.47,
                'bubefsm30': 0.47,
                'bubefs_1h': 1.74
            },
            {
                'symbol': 'MSFT',
                'bubefsm2': 1.74,
                'bubefsm5': 1.74,
                'bubefsm15': 1.74,
                'bubefsm30': 1.74,
                'bubefs_1h': 1.74
            },
            {
                'symbol': 'AAPL',
                'bubefsm2': 0.85,
                'bubefsm5': 0.85,
                'bubefsm15': 0.85,
                'bubefsm30': 0.85,
                'bubefs_1h': 0.85
            }
        ]
    }
    
    print("🧪 Testing MACD Multi-TF US BACKFILL mode")
    print("📊 BuBeFSM Analysis: Bull, Bear, FastMACD, SignalMACD, M (timeframe)")
    print("🎯 Logic: (FastMACD >= threshold OR SignalMACD >= threshold) AND both positive = BULL")
    print("⏰ Timeframes: 2m, 5m, 15m, 30m, 1h")
    print("📅 Backfill: 1 year of historical data")
    print("=" * 60)
    
    # Execute backfill pipeline
    result = job_macd_multi_us_pipeline(workflow_config, mode='backfill')
    
    print(f"✅ Backfill result: {result}")
    
    if isinstance(result, dict) and result.get('status') == 'success':
        print(f"📈 Mode: {result['mode']}")
        print(f"📊 Symbols processed: {result['symbols_processed']}")
        print(f"🎯 Signals generated: {result['signals_generated']}")
        
        # Show detailed results for each symbol
        for symbol_result in result.get('results', []):
            symbol = symbol_result['symbol']
            result_data = symbol_result['result']
            
            if isinstance(result_data, dict) and result_data.get('status') == 'success':
                overall = result_data.get('overall_signal', {})
                print(f"\n📊 {symbol}:")
                print(f"   Signal: {overall.get('signal_type', 'N/A')}")
                print(f"   Confidence: {overall.get('confidence', 0):.2f}")
                print(f"   Bull/Bear: {overall.get('bull_count', 0)}/{overall.get('bear_count', 0)}")
                
                # Show timeframe details
                timeframes = result_data.get('timeframe_results', {})
                for tf, tf_result in timeframes.items():
                    bubefsm = tf_result.get('bubefsm', {})
                    print(f"   {tf}: {bubefsm.get('signal_type', 'N/A')} "
                          f"(FastMACD: {tf_result.get('fast_macd', 0):.3f}, "
                          f"SignalMACD: {tf_result.get('signal_macd', 0):.3f}, "
                          f"Threshold: {tf_result.get('threshold', 0):.3f})")
            else:
                print(f"\n❌ {symbol}: {result_data}")
    else:
        print(f"⚠️ Backfill returned: {result}")

def test_realtime_mode():
    """Test MACD Multi-TF US realtime mode"""
    print("\n" + "=" * 60)
    print("🧪 Testing MACD Multi-TF US REALTIME mode")
    
    workflow_config = {
        'fastPeriod': 7,
        'slowPeriod': 113,
        'signalPeriod': 144,
        'symbolThresholds': [
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
    
    result = job_macd_multi_us_pipeline(workflow_config, mode='realtime')
    print(f"✅ Realtime result: {result}")

if __name__ == "__main__":
    print("🚀 Starting MACD Multi-TF US backfill tests...")
    print("📋 BuBeFSM = Bull, Bear, FastMACD, SignalMACD, M (timeframe)")
    print("🎯 Logic: (FastMACD >= threshold OR SignalMACD >= threshold) AND both positive = BULL")
    print("⚠️  Note: This will backfill 1 year of data for each symbol")
    
    try:
        test_backfill_mode()
        test_realtime_mode()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
