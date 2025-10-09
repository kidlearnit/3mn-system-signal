#!/usr/bin/env python3
"""
Simple test for Flexible Multi-Indicator System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.flexible_multi_indicator_service import FlexibleMultiIndicatorService
import json

def test_flexible_simple():
    """Simple test for flexible multi-indicator system"""
    print("🧪 Simple Test for Flexible Multi-Indicator System")
    print("=" * 50)
    
    # Initialize service
    service = FlexibleMultiIndicatorService()
    
    # Test 1: Get available indicators
    print("\n📊 Test 1: Available Indicators")
    indicators = service.get_available_indicators()
    print(f"Available indicators: {list(indicators.keys())}")
    
    # Test 2: Validate configuration
    print("\n✅ Test 2: Configuration Validation")
    test_config = {
        'symbols': ['AAPL'],
        'symbolConfigs': {
            'AAPL': {
                'indicators': [
                    {'type': 'macd_multi', 'enabled': True, 'weight': 0.3},
                    {'type': 'sma', 'enabled': True, 'weight': 0.25},
                    {'type': 'rsi', 'enabled': True, 'weight': 0.2},
                    {'type': 'bollinger', 'enabled': True, 'weight': 0.25}
                ]
            }
        },
        'aggregation': {
            'method': 'weighted_average',
            'minIndicators': 3,
            'consensusThreshold': 0.7,
            'confidenceThreshold': 0.6
        }
    }
    
    validation_result = service.validate_configuration(test_config)
    print(f"Configuration valid: {validation_result['valid']}")
    if validation_result['errors']:
        print(f"Errors: {validation_result['errors']}")
    if validation_result['warnings']:
        print(f"Warnings: {validation_result['warnings']}")
    
    # Test 3: Test individual symbol analysis
    print("\n🔍 Test 3: Individual Symbol Analysis")
    try:
        symbol_result = service.analyze_symbol('AAPL', test_config['symbolConfigs']['AAPL']['indicators'])
        print(f"Symbol: {symbol_result.get('symbol', 'Unknown')}")
        print(f"Signals count: {len(symbol_result.get('signals', []))}")
        print(f"Has error: {'error' in symbol_result}")
        
        if symbol_result.get('signals'):
            for signal in symbol_result['signals']:
                print(f"  - {signal['type']}: {signal['signal_type']} (confidence: {signal['confidence']:.2f})")
        
    except Exception as e:
        print(f"Symbol analysis failed: {str(e)}")
    
    print("\n✅ Simple test completed!")

if __name__ == "__main__":
    test_flexible_simple()
