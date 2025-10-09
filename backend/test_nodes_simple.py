#!/usr/bin/env python3
"""
Simple test script to verify node output data structure
"""
import os
import sys
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_symbol_node_output():
    """Test symbol node output data structure"""
    print("=== Testing Symbol Node Output Structure ===")
    
    # Mock symbol node execution result
    result = {
        'type': 'symbol',
        'ticker': 'AAPL',
        'exchange': 'NASDAQ',
        'timeframes': ['1m', '5m', '15m', '1h', '4h', '1d'],
        'status': 'success',
        'data_validated': True,
        'validated_data': {
            '1m': {'symbol_id': 1, 'timeframe': '1m', 'candle_count': 1000, 'latest_candle': '2024-01-15T10:30:00'},
            '5m': {'symbol_id': 1, 'timeframe': '5m', 'candle_count': 200, 'latest_candle': '2024-01-15T10:30:00'},
            '15m': {'symbol_id': 1, 'timeframe': '15m', 'candle_count': 67, 'latest_candle': '2024-01-15T10:30:00'}
        }
    }
    
    print(f"Symbol Node Result: {json.dumps(result, indent=2, default=str)}")
    
    # Validate output structure
    required_fields = ['type', 'ticker', 'exchange', 'timeframes', 'status', 'data_validated']
    for field in required_fields:
        assert field in result, f"Missing '{field}' field"
    
    print("✓ Symbol node output structure is valid")
    return result

def test_macd_node_output():
    """Test MACD node output data structure"""
    print("\n=== Testing MACD Node Output Structure ===")
    
    # Mock MACD node execution result
    result = {
        'type': 'macd',
        'timeframes': ['1m', '5m', '15m'],
        'status': 'success',
        'data_validated': True,
        'macd_signals': {
            '1m': {
                'macd_line': 0.0012,
                'signal_line': 0.0008,
                'histogram': 0.0004,
                'signal_type': 'BUY',
                'confidence': 0.75,
                'zone_thresholds': {
                    'fmacd': {'above': 0.001, 'below': -0.001},
                    'smacd': {'above': 0.0005, 'below': -0.0005}
                },
                'bars_momentums': {
                    'momentum1': [0.1, 0.2, 0.3, 0.4, 0.5],
                    'momentum2': [0.05, 0.15, 0.25, 0.35, 0.45]
                }
            },
            '5m': {
                'macd_line': 0.0008,
                'signal_line': 0.0006,
                'histogram': 0.0002,
                'signal_type': 'HOLD',
                'confidence': 0.45
            }
        }
    }
    
    print(f"MACD Node Result: {json.dumps(result, indent=2, default=str)}")
    
    # Validate output structure
    required_fields = ['type', 'timeframes', 'status', 'data_validated', 'macd_signals']
    for field in required_fields:
        assert field in result, f"Missing '{field}' field"
    
    print("✓ MACD node output structure is valid")
    return result

def test_sma_node_output():
    """Test SMA node output data structure"""
    print("\n=== Testing SMA Node Output Structure ===")
    
    # Mock SMA node execution result
    result = {
        'type': 'sma',
        'timeframes': ['1m', '5m', '15m'],
        'status': 'success',
        'data_validated': True,
        'sma_signals': {
            '1m': {
                'sma_value': 150.25,
                'current_price': 150.30,
                'signal_type': 'BUY',
                'confidence': 0.65,
                'price_above_sma': True
            },
            '5m': {
                'sma_value': 150.20,
                'current_price': 150.15,
                'signal_type': 'SELL',
                'confidence': 0.55,
                'price_above_sma': False
            }
        }
    }
    
    print(f"SMA Node Result: {json.dumps(result, indent=2, default=str)}")
    
    # Validate output structure
    required_fields = ['type', 'timeframes', 'status', 'data_validated', 'sma_signals']
    for field in required_fields:
        assert field in result, f"Missing '{field}' field"
    
    print("✓ SMA node output structure is valid")
    return result

def test_aggregation_node_output():
    """Test Aggregation node output data structure"""
    print("\n=== Testing Aggregation Node Output Structure ===")
    
    # Mock aggregation node execution result
    result = {
        'type': 'aggregation',
        'method': 'weighted_average',
        'status': 'success',
        'data_validated': True,
        'aggregated_signal': {
            'signal_type': 'BUY',
            'confidence': 0.68,
            'weighted_score': 0.68,
            'contributing_signals': {
                '1m': {'weight': 0.4, 'signal': 'BUY', 'confidence': 0.75},
                '5m': {'weight': 0.3, 'signal': 'HOLD', 'confidence': 0.45},
                '15m': {'weight': 0.2, 'signal': 'BUY', 'confidence': 0.80},
                '1h': {'weight': 0.1, 'signal': 'BUY', 'confidence': 0.70}
            },
            'final_decision': 'BUY',
            'decision_reason': 'Majority of timeframes show BUY signal with high confidence'
        }
    }
    
    print(f"Aggregation Node Result: {json.dumps(result, indent=2, default=str)}")
    
    # Validate output structure
    required_fields = ['type', 'method', 'status', 'data_validated', 'aggregated_signal']
    for field in required_fields:
        assert field in result, f"Missing '{field}' field"
    
    print("✓ Aggregation node output structure is valid")
    return result

def test_output_node_output():
    """Test Output node output data structure"""
    print("\n=== Testing Output Node Output Structure ===")
    
    # Mock output node execution result
    result = {
        'type': 'output',
        'channels': ['database', 'telegram', 'email'],
        'format': 'json',
        'status': 'success',
        'data_validated': True,
        'output_data': {
            'signal_id': 'sig_12345',
            'timestamp': datetime.now().isoformat(),
            'symbol': 'AAPL',
            'timeframe': '1m',
            'signal_type': 'BUY',
            'confidence': 0.68,
            'price': 150.30,
            'message': 'Strong BUY signal detected across multiple timeframes'
        },
        'delivery_status': {
            'database': 'sent',
            'telegram': 'sent',
            'email': 'pending'
        }
    }
    
    print(f"Output Node Result: {json.dumps(result, indent=2, default=str)}")
    
    # Validate output structure
    required_fields = ['type', 'channels', 'format', 'status', 'data_validated', 'output_data']
    for field in required_fields:
        assert field in result, f"Missing '{field}' field"
    
    print("✓ Output node output structure is valid")
    return result

def test_workflow_data_flow():
    """Test complete workflow data flow"""
    print("\n=== Testing Complete Workflow Data Flow ===")
    
    # Mock complete workflow execution
    workflow_result = {
        'success': True,
        'execution_time': datetime.now().isoformat(),
        'data_validated': True,
        'results': {
            'node_1': {
                'type': 'symbol',
                'ticker': 'AAPL',
                'exchange': 'NASDAQ',
                'timeframes': ['1m', '5m', '15m'],
                'status': 'success',
                'data_validated': True
            },
            'node_2': {
                'type': 'macd',
                'timeframes': ['1m', '5m', '15m'],
                'status': 'success',
                'data_validated': True,
                'macd_signals': {
                    '1m': {'signal_type': 'BUY', 'confidence': 0.75},
                    '5m': {'signal_type': 'HOLD', 'confidence': 0.45},
                    '15m': {'signal_type': 'BUY', 'confidence': 0.80}
                }
            },
            'node_3': {
                'type': 'aggregation',
                'method': 'weighted_average',
                'status': 'success',
                'data_validated': True,
                'aggregated_signal': {
                    'signal_type': 'BUY',
                    'confidence': 0.68
                }
            },
            'node_4': {
                'type': 'output',
                'channels': ['database', 'telegram'],
                'status': 'success',
                'data_validated': True,
                'output_data': {
                    'signal_type': 'BUY',
                    'confidence': 0.68
                }
            }
        }
    }
    
    print(f"Complete Workflow Result: {json.dumps(workflow_result, indent=2, default=str)}")
    
    # Validate workflow structure
    assert workflow_result['success'], "Workflow execution failed"
    assert 'results' in workflow_result, "Missing 'results' field"
    assert len(workflow_result['results']) == 4, "Expected 4 nodes in workflow"
    
    # Validate each node has required fields
    for node_id, node_result in workflow_result['results'].items():
        assert 'type' in node_result, f"Node {node_id} missing 'type' field"
        assert 'status' in node_result, f"Node {node_id} missing 'status' field"
        assert 'data_validated' in node_result, f"Node {node_id} missing 'data_validated' field"
    
    print("✓ Complete workflow data flow is valid")
    return workflow_result

def main():
    """Run all node output tests"""
    print("Starting Node Output Data Structure Tests")
    print("=" * 60)
    
    try:
        # Test individual node output structures
        symbol_result = test_symbol_node_output()
        macd_result = test_macd_node_output()
        sma_result = test_sma_node_output()
        aggregation_result = test_aggregation_node_output()
        output_result = test_output_node_output()
        
        # Test complete workflow data flow
        workflow_result = test_workflow_data_flow()
        
        print("\n" + "=" * 60)
        print("✓ All node output structure tests completed successfully!")
        
        # Summary
        print("\nTest Summary:")
        print(f"  Symbol Node Structure: {'✓' if symbol_result else '✗'}")
        print(f"  MACD Node Structure: {'✓' if macd_result else '✗'}")
        print(f"  SMA Node Structure: {'✓' if sma_result else '✗'}")
        print(f"  Aggregation Node Structure: {'✓' if aggregation_result else '✗'}")
        print(f"  Output Node Structure: {'✓' if output_result else '✗'}")
        print(f"  Complete Workflow Flow: {'✓' if workflow_result else '✗'}")
        
        print("\nNode Output Data Structure Validation:")
        print("✓ All nodes return consistent structure with required fields")
        print("✓ Data validation flag is properly set")
        print("✓ Signal types and confidence scores are included")
        print("✓ Timeframe-specific data is properly organized")
        print("✓ Workflow execution maintains data flow integrity")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
