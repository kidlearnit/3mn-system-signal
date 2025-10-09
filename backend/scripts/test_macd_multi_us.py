#!/usr/bin/env python3
"""
Test script for MACD Multi-TF US functionality
BuBeFSM = Bull, Bear, FastMACD, SignalMACD, M (timeframe)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from worker.macd_multi_us_jobs import job_macd_multi_us_pipeline

def test_macd_multi_us_pipeline():
    """Test MACD Multi-TF US pipeline with 25 symbols"""
    
    # Sample workflow configuration with 25 US symbols
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
            },
            {
                'symbol': 'AMZN',
                'bubefsm2': 0.92,
                'bubefsm5': 0.92,
                'bubefsm15': 0.92,
                'bubefsm30': 0.92,
                'bubefs_1h': 0.92
            },
            {
                'symbol': 'AVGO',
                'bubefsm2': 0.68,
                'bubefsm5': 0.68,
                'bubefsm15': 0.68,
                'bubefsm30': 0.68,
                'bubefs_1h': 0.68
            },
            {
                'symbol': 'META',
                'bubefsm2': 1.15,
                'bubefsm5': 1.15,
                'bubefsm15': 1.15,
                'bubefsm30': 1.15,
                'bubefs_1h': 1.15
            },
            {
                'symbol': 'NFLX',
                'bubefsm2': 0.73,
                'bubefsm5': 0.73,
                'bubefsm15': 0.73,
                'bubefsm30': 0.73,
                'bubefs_1h': 0.73
            },
            {
                'symbol': 'TSLA',
                'bubefsm2': 1.28,
                'bubefsm5': 1.28,
                'bubefsm15': 1.28,
                'bubefsm30': 1.28,
                'bubefs_1h': 1.28
            },
            {
                'symbol': 'GOOGL',
                'bubefsm2': 0.95,
                'bubefsm5': 0.95,
                'bubefsm15': 0.95,
                'bubefsm30': 0.95,
                'bubefs_1h': 0.95
            },
            {
                'symbol': 'GOOG',
                'bubefsm2': 0.95,
                'bubefsm5': 0.95,
                'bubefsm15': 0.95,
                'bubefsm30': 0.95,
                'bubefs_1h': 0.95
            }
            # Add more symbols as needed for full 25
        ]
    }
    
    print("🧪 Testing MACD Multi-TF US pipeline with 10 symbols")
    print("📊 BuBeFSM Analysis: Bull, Bear, FastMACD, SignalMACD, M (timeframe)")
    print("🎯 Logic: (FastMACD >= threshold OR SignalMACD >= threshold) AND both positive = BULL")
    print("⏰ Timeframes: 2m, 5m, 15m, 30m, 1h")
    print("=" * 60)
    
    # Execute pipeline
    result = job_macd_multi_us_pipeline(workflow_config)
    
    print(f"✅ Pipeline result: {result}")
    
    if isinstance(result, dict) and result.get('status') == 'success':
        print(f"📈 Symbols processed: {result['symbols_processed']}")
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
        print(f"⚠️ Pipeline returned: {result}")

def test_single_symbol():
    """Test single symbol processing"""
    print("\n" + "=" * 60)
    print("🧪 Testing single symbol (NVDA)")
    
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
    
    result = job_macd_multi_us_pipeline(workflow_config)
    print(f"✅ Single symbol result: {result}")

if __name__ == "__main__":
    print("🚀 Starting MACD Multi-TF US tests...")
    print("📋 BuBeFSM = Bull, Bear, FastMACD, SignalMACD, M (timeframe)")
    print("🎯 Logic: (FastMACD >= threshold OR SignalMACD >= threshold) AND both positive = BULL")
    
    try:
        test_macd_multi_us_pipeline()
        test_single_symbol()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
