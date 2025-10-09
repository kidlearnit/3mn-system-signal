#!/usr/bin/env python3
"""
Simple MACD test với 1 symbol
"""

import os
import sys
import json

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def simple_macd_test():
    """Simple MACD test"""
    
    print("🧪 SIMPLE MACD TEST")
    print("=" * 40)
    
    # Test với AAPL
    test_symbol = "AAPL"
    print(f"📊 Testing với symbol: {test_symbol}")
    
    # Tạo workflow config
    workflow_config = {
        'fastPeriod': 7,
        'slowPeriod': 113,
        'signalPeriod': 144,
        'symbolThresholds': [
            {
                'symbol': test_symbol,
                'bubefsm2': 0.85,
                'bubefsm5': 0.85,
                'bubefsm15': 0.85,
                'bubefsm30': 0.85,
                'bubefs_1h': 0.85
            }
        ]
    }
    
    try:
        # Import và test
        print("1. Importing modules...")
        from worker.macd_multi_us_jobs import job_macd_multi_us_pipeline
        print("✅ Import OK")
        
        print("2. Testing backfill mode...")
        result = job_macd_multi_us_pipeline(workflow_config, 'backfill')
        print(f"📈 Result: {json.dumps(result, indent=2, default=str)}")
        
        if result.get('status') == 'success':
            print("✅ Backfill SUCCESS")
            
            # Kiểm tra có lỗi không
            results = result.get('results', [])
            if results and results[0].get('result') == 'error':
                print(f"⚠️  Error: {results[0].get('error')}")
                return False
            else:
                print("✅ No errors found")
                return True
        else:
            print(f"❌ Backfill FAILED: {result}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = simple_macd_test()
    if success:
        print(f"\n🎉 TEST PASSED!")
    else:
        print(f"\n❌ TEST FAILED!")
    sys.exit(0 if success else 1)
