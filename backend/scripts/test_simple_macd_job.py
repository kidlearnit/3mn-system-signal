#!/usr/bin/env python3
"""
Test simple MACD Multi-TF job with real data
"""

import os
import sys
sys.path.append('/code')

from worker.macd_multi_us_jobs import job_macd_multi_us_pipeline

def test_simple_macd_job():
    """Test simple MACD Multi-TF job"""
    print("🧪 Testing Simple MACD Multi-TF Job")
    print("=" * 50)
    
    # Simple config with just a few symbols
    config = {
        'fastPeriod': 7,
        'slowPeriod': 113,
        'signalPeriod': 144,
        'symbolThresholds': [
            {
                'symbol': 'AAPL',
                'company': 'Apple Inc.',
                'weight': '7.33%',
                'sector': 'Technology',
                'bubefsm1': 0.33,
                'bubefsm2': 0.74,
                'bubefsm5': 1.0,
                'bubefsm15': 1.47,
                'bubefsm30': 1.74,
                'bubefs_1h': 2.2
            },
            {
                'symbol': 'MSFT',
                'company': 'Microsoft Corporation',
                'weight': '8.98%',
                'sector': 'Technology',
                'bubefsm1': 0.33,
                'bubefsm2': 0.74,
                'bubefsm5': 1.0,
                'bubefsm15': 1.47,
                'bubefsm30': 1.74,
                'bubefs_1h': 2.2
            }
        ]
    }
    
    try:
        print("📊 Testing with 2 symbols: AAPL, MSFT")
        print(f"Config: {config}")
        
        # Test in realtime mode
        result = job_macd_multi_us_pipeline(config, mode='realtime')
        
        print(f"\n✅ Job completed successfully!")
        print(f"Result: {result}")
        
        if isinstance(result, dict):
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Symbols processed: {result.get('symbols_processed', 0)}")
            print(f"Signals generated: {result.get('signals_generated', 0)}")
            print(f"Errors: {result.get('errors', 0)}")
            
            if 'details' in result:
                print(f"\n📋 Processing Details:")
                for detail in result['details']:
                    symbol = detail.get('symbol', 'Unknown')
                    status = detail.get('status', 'Unknown')
                    print(f"  {symbol}: {status}")
        
    except Exception as e:
        print(f"❌ Error running job: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_macd_job()
