#!/usr/bin/env python3
"""
Test script for Flexible Multi-Indicator API
"""

import requests
import json

def test_flexible_api():
    """Test the flexible multi-indicator API"""
    print("🧪 Testing Flexible Multi-Indicator API")
    print("=" * 50)
    
    base_url = "http://localhost:5010"
    
    # Test 1: Get available indicators
    print("\n📊 Test 1: Get Available Indicators")
    try:
        response = requests.get(f"{base_url}/api/flexible-multi-indicator/indicators")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {len(data['indicators'])} indicators available")
            for indicator_type, config in data['indicators'].items():
                print(f"  - {indicator_type}: {config['name']}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test 2: Validate configuration
    print("\n✅ Test 2: Validate Configuration")
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
    
    try:
        response = requests.post(
            f"{base_url}/api/flexible-multi-indicator/validate",
            json=test_config
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Configuration valid: {data['valid']}")
            if data.get('errors'):
                print(f"Errors: {data['errors']}")
            if data.get('warnings'):
                print(f"Warnings: {data['warnings']}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test 3: Execute workflow
    print("\n🚀 Test 3: Execute Workflow")
    try:
        response = requests.post(
            f"{base_url}/api/flexible-multi-indicator/execute",
            json=test_config
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Workflow executed successfully")
            print(f"Total symbols: {data['summary']['total_symbols']}")
            print(f"Signals generated: {data['summary']['signals_generated']}")
            print(f"Aggregation method: {data['summary']['aggregation_method']}")
            
            # Show results for each symbol
            for result in data['results']:
                symbol = result.get('symbol', 'Unknown')
                signals_count = len(result.get('signals', []))
                has_aggregated = result.get('aggregated_signal') is not None
                print(f"  - {symbol}: {signals_count} signals, aggregated: {has_aggregated}")
                
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test 4: Analyze single symbol
    print("\n🔍 Test 4: Analyze Single Symbol")
    try:
        symbol_config = {
            'indicators': [
                {'type': 'macd_multi', 'enabled': True, 'weight': 0.3},
                {'type': 'sma', 'enabled': True, 'weight': 0.25},
                {'type': 'rsi', 'enabled': True, 'weight': 0.2},
                {'type': 'bollinger', 'enabled': True, 'weight': 0.25}
            ]
        }
        
        response = requests.post(
            f"{base_url}/api/flexible-multi-indicator/symbols/AAPL/analyze",
            json=symbol_config
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Symbol analysis successful")
            print(f"Symbol: {data['symbol']}")
            print(f"Signals count: {len(data['result'].get('signals', []))}")
            
            # Show individual signals
            for signal in data['result'].get('signals', []):
                print(f"  - {signal['type']}: {signal['signal_type']} (confidence: {signal['confidence']:.2f})")
                
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n✅ Flexible Multi-Indicator API tests completed!")

if __name__ == "__main__":
    test_flexible_api()
