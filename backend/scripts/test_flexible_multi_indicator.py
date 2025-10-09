#!/usr/bin/env python3
"""
Test script for Flexible Multi-Indicator System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.flexible_multi_indicator_service import FlexibleMultiIndicatorService
import json

def test_flexible_multi_indicator():
    """Test the flexible multi-indicator system"""
    print("🧪 Testing Flexible Multi-Indicator System")
    print("=" * 50)
    
    # Initialize service
    service = FlexibleMultiIndicatorService()
    
    # Test 1: Get available indicators
    print("\n📊 Test 1: Available Indicators")
    indicators = service.get_available_indicators()
    print(f"Available indicators: {list(indicators.keys())}")
    for indicator_type, config in indicators.items():
        print(f"  - {indicator_type}: {config['name']} (weight: {config['weight']})")
    
    # Test 2: Validate configuration
    print("\n✅ Test 2: Configuration Validation")
    test_config = {
        'symbols': ['AAPL', 'MSFT'],
        'symbolConfigs': {
            'AAPL': {
                'indicators': [
                    {'type': 'macd_multi', 'enabled': True, 'weight': 0.3},
                    {'type': 'sma', 'enabled': True, 'weight': 0.25},
                    {'type': 'rsi', 'enabled': True, 'weight': 0.2},
                    {'type': 'bollinger', 'enabled': True, 'weight': 0.25}
                ]
            },
            'MSFT': {
                'indicators': [
                    {'type': 'macd_multi', 'enabled': True, 'weight': 0.4},
                    {'type': 'sma', 'enabled': True, 'weight': 0.3},
                    {'type': 'rsi', 'enabled': True, 'weight': 0.3}
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
    
    # Test 3: Invalid configuration
    print("\n❌ Test 3: Invalid Configuration")
    invalid_config = {
        'symbols': ['AAPL'],
        'symbolConfigs': {
            'AAPL': {
                'indicators': [
                    {'type': 'macd_multi', 'enabled': True, 'weight': 0.5},
                    {'type': 'sma', 'enabled': True, 'weight': 0.5}
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
    
    validation_result = service.validate_configuration(invalid_config)
    print(f"Configuration valid: {validation_result['valid']}")
    if validation_result['errors']:
        print(f"Errors: {validation_result['errors']}")
    
    # Test 4: Execute workflow (mock data)
    print("\n🚀 Test 4: Workflow Execution")
    try:
        # This would normally fetch real data, but we'll test the structure
        results = service.execute_workflow(
            test_config['symbols'],
            test_config['symbolConfigs'],
            test_config['aggregation']
        )
        
        print(f"Workflow executed for {len(results)} symbols")
        for result in results:
            symbol = result.get('symbol', 'Unknown')
            signals_count = len(result.get('signals', []))
            has_aggregated = result.get('aggregated_signal') is not None
            print(f"  - {symbol}: {signals_count} signals, aggregated: {has_aggregated}")
            
    except Exception as e:
        print(f"Workflow execution test failed (expected): {str(e)}")
    
    print("\n✅ Flexible Multi-Indicator System tests completed!")

if __name__ == "__main__":
    test_flexible_multi_indicator()
