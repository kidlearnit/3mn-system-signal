#!/usr/bin/env python3
"""
Test script to verify node output data in workflow execution
"""
import os
import sys
import json
import requests
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.db import SessionLocal
from app.services.data_validation import DataValidator
from app.routes.workflow_api import (
    execute_symbol_node, 
    execute_macd_node, 
    execute_sma_node, 
    execute_aggregation_node, 
    execute_output_node
)

def test_symbol_node_output():
    """Test symbol node output data"""
    print("=== Testing Symbol Node Output ===")
    
    # Mock properties for symbol node
    properties = {
        'ticker': 'AAPL',
        'exchange': 'NASDAQ',
        'timeframes': ['1m', '5m', '15m', '1h', '4h', '1d'],
        'limit': 100
    }
    
    validator = DataValidator()
    result = execute_symbol_node(properties, validator)
    
    print(f"Symbol Node Result: {json.dumps(result, indent=2, default=str)}")
    
    # Validate output structure
    assert 'type' in result, "Missing 'type' field"
    assert 'ticker' in result, "Missing 'ticker' field"
    assert 'timeframes' in result, "Missing 'timeframes' field"
    assert 'data_validated' in result, "Missing 'data_validated' field"
    
    print("✓ Symbol node output structure is valid")
    return result

def test_macd_node_output():
    """Test MACD node output data"""
    print("\n=== Testing MACD Node Output ===")
    
    # Mock properties for MACD node
    properties = {
        'fast_period': 12,
        'slow_period': 26,
        'signal_period': 9,
        'timeframes': ['1m', '5m', '15m'],
        'min_confidence': 0.6,
        'matrixData': {
            '1m': {
                'macd_params': {'fast': 12, 'slow': 26, 'signal': 9},
                'min_confidence': 0.6,
                'zone_thresholds': {
                    'fmacd': {'above': 0.001, 'below': -0.001},
                    'smacd': {'above': 0.0005, 'below': -0.0005}
                },
                'bars_momentums': {
                    'momentum1': [0.1, 0.2, 0.3, 0.4, 0.5],
                    'momentum2': [0.05, 0.15, 0.25, 0.35, 0.45]
                }
            }
        }
    }
    
    validator = DataValidator()
    result = execute_macd_node(properties, validator)
    
    print(f"MACD Node Result: {json.dumps(result, indent=2, default=str)}")
    
    # Validate output structure
    assert 'type' in result, "Missing 'type' field"
    assert 'timeframes' in result, "Missing 'timeframes' field"
    assert 'data_validated' in result, "Missing 'data_validated' field"
    
    print("✓ MACD node output structure is valid")
    return result

def test_sma_node_output():
    """Test SMA node output data"""
    print("\n=== Testing SMA Node Output ===")
    
    # Mock properties for SMA node
    properties = {
        'period': 20,
        'timeframes': ['1m', '5m', '15m'],
        'min_confidence': 0.5
    }
    
    validator = DataValidator()
    result = execute_sma_node(properties, validator)
    
    print(f"SMA Node Result: {json.dumps(result, indent=2, default=str)}")
    
    # Validate output structure
    assert 'type' in result, "Missing 'type' field"
    assert 'timeframes' in result, "Missing 'timeframes' field"
    assert 'data_validated' in result, "Missing 'data_validated' field"
    
    print("✓ SMA node output structure is valid")
    return result

def test_aggregation_node_output():
    """Test Aggregation node output data"""
    print("\n=== Testing Aggregation Node Output ===")
    
    # Mock properties for aggregation node
    properties = {
        'method': 'weighted_average',
        'weights': {'1m': 0.4, '5m': 0.3, '15m': 0.2, '1h': 0.1},
        'min_confidence': 0.6
    }
    
    # Mock node_map and connections
    node_map = {
        'node_1': {'type': 'symbol', 'id': 'node_1'},
        'node_2': {'type': 'macd', 'id': 'node_2'},
        'node_3': {'type': 'sma', 'id': 'node_3'}
    }
    connections = [
        {'from': {'nodeId': 'node_1'}, 'to': {'nodeId': 'node_2'}},
        {'from': {'nodeId': 'node_2'}, 'to': {'nodeId': 'node_3'}}
    ]
    
    validator = DataValidator()
    result = execute_aggregation_node(properties, node_map, connections, validator)
    
    print(f"Aggregation Node Result: {json.dumps(result, indent=2, default=str)}")
    
    # Validate output structure
    assert 'type' in result, "Missing 'type' field"
    assert 'method' in result, "Missing 'method' field"
    assert 'data_validated' in result, "Missing 'data_validated' field"
    
    print("✓ Aggregation node output structure is valid")
    return result

def test_output_node_output():
    """Test Output node output data"""
    print("\n=== Testing Output Node Output ===")
    
    # Mock properties for output node
    properties = {
        'channels': ['database', 'telegram', 'email'],
        'format': 'json',
        'autoStart': True
    }
    
    validator = DataValidator()
    result = execute_output_node(properties, validator)
    
    print(f"Output Node Result: {json.dumps(result, indent=2, default=str)}")
    
    # Validate output structure
    assert 'type' in result, "Missing 'type' field"
    assert 'channels' in result, "Missing 'channels' field"
    assert 'format' in result, "Missing 'format' field"
    assert 'data_validated' in result, "Missing 'data_validated' field"
    
    print("✓ Output node output structure is valid")
    return result

def test_workflow_execution_api():
    """Test workflow execution via API"""
    print("\n=== Testing Workflow Execution API ===")
    
    # First, create a test workflow
    test_workflow = {
        'name': 'Test Workflow for Node Output',
        'description': 'Testing node output data',
        'nodes': [
            {
                'id': 'node_1',
                'type': 'symbol',
                'position': {'x': 100, 'y': 100},
                'properties': {
                    'ticker': 'AAPL',
                    'exchange': 'NASDAQ',
                    'timeframes': ['1m', '5m', '15m']
                }
            },
            {
                'id': 'node_2',
                'type': 'macd',
                'position': {'x': 300, 'y': 100},
                'properties': {
                    'fast_period': 12,
                    'slow_period': 26,
                    'signal_period': 9,
                    'timeframes': ['1m', '5m', '15m'],
                    'min_confidence': 0.6
                }
            },
            {
                'id': 'node_3',
                'type': 'output',
                'position': {'x': 500, 'y': 100},
                'properties': {
                    'channels': ['database'],
                    'format': 'json'
                }
            }
        ],
        'connections': [
            {
                'from': {'nodeId': 'node_1'},
                'to': {'nodeId': 'node_2'}
            },
            {
                'from': {'nodeId': 'node_2'},
                'to': {'nodeId': 'node_3'}
            }
        ]
    }
    
    try:
        # Save workflow
        response = requests.post('http://localhost:5010/api/workflow/save', 
                               json=test_workflow,
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            workflow_data = response.json()
            workflow_id = workflow_data.get('id') or workflow_data.get('workflow_id')
            print(f"✓ Test workflow created with ID: {workflow_id}")
            
            # Execute workflow
            exec_response = requests.post(f'http://localhost:5010/api/workflow/execute/{workflow_id}')
            
            if exec_response.status_code == 200:
                exec_result = exec_response.json()
                print(f"✓ Workflow executed successfully")
                print(f"Execution Result: {json.dumps(exec_result, indent=2, default=str)}")
                
                # Check node results
                if 'result' in exec_result and 'results' in exec_result['result']:
                    node_results = exec_result['result']['results']
                    print(f"\nNode Results Summary:")
                    for node_id, result in node_results.items():
                        print(f"  {node_id}: {result.get('type', 'unknown')} - {result.get('status', 'unknown')}")
                
                return exec_result
            else:
                print(f"✗ Workflow execution failed: {exec_response.status_code}")
                print(f"Error: {exec_response.text}")
        else:
            print(f"✗ Failed to create test workflow: {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to API server. Make sure the web service is running on localhost:5010")
    except Exception as e:
        print(f"✗ API test failed: {e}")
    
    return None

def test_data_validation():
    """Test data validation service"""
    print("\n=== Testing Data Validation Service ===")
    
    validator = DataValidator()
    
    # Test environment validation
    env_result = validator.validate_execution_environment()
    print(f"Environment Validation: {json.dumps(env_result, indent=2, default=str)}")
    
    # Test data snapshot
    try:
        snapshot = validator.get_data_snapshot(symbol_id=1, timeframe='1m', limit=10)
        print(f"Data Snapshot: {json.dumps(snapshot, indent=2, default=str)}")
    except Exception as e:
        print(f"Data snapshot test failed: {e}")
    
    print("✓ Data validation service tested")

def main():
    """Run all node output tests"""
    print("Starting Node Output Data Tests")
    print("=" * 50)
    
    try:
        # Test individual nodes
        symbol_result = test_symbol_node_output()
        macd_result = test_macd_node_output()
        sma_result = test_sma_node_output()
        aggregation_result = test_aggregation_node_output()
        output_result = test_output_node_output()
        
        # Test data validation
        test_data_validation()
        
        # Test workflow execution via API
        api_result = test_workflow_execution_api()
        
        print("\n" + "=" * 50)
        print("✓ All node output tests completed successfully!")
        
        # Summary
        print("\nTest Summary:")
        print(f"  Symbol Node: {'✓' if symbol_result else '✗'}")
        print(f"  MACD Node: {'✓' if macd_result else '✗'}")
        print(f"  SMA Node: {'✓' if sma_result else '✗'}")
        print(f"  Aggregation Node: {'✓' if aggregation_result else '✗'}")
        print(f"  Output Node: {'✓' if output_result else '✗'}")
        print(f"  API Execution: {'✓' if api_result else '✗'}")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
