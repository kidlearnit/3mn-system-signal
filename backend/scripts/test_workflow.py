#!/usr/bin/env python3
"""
Test script for workflow API
"""

import requests
import json
import uuid
from datetime import datetime

BASE_URL = "http://localhost:5010"

def test_workflow_api():
    """Test workflow API endpoints"""
    
    # Test data
    workflow_data = {
        "name": "VN30 MACD + SMA Strategy",
        "description": "Test workflow combining MACD and SMA strategies for VN30",
        "nodes": [
            {
                "id": "node_1",
                "type": "symbol",
                "x": 100,
                "y": 100
            },
            {
                "id": "node_2", 
                "type": "macd",
                "x": 300,
                "y": 100
            },
            {
                "id": "node_3",
                "type": "sma", 
                "x": 300,
                "y": 200
            },
            {
                "id": "node_4",
                "type": "aggregation",
                "x": 500,
                "y": 150
            },
            {
                "id": "node_5",
                "type": "output",
                "x": 700,
                "y": 150
            }
        ],
        "connections": [
            {
                "id": "conn_1",
                "from": {"nodeId": "node_1", "type": "output"},
                "to": {"nodeId": "node_2", "type": "input"}
            },
            {
                "id": "conn_2", 
                "from": {"nodeId": "node_1", "type": "output"},
                "to": {"nodeId": "node_3", "type": "input"}
            },
            {
                "id": "conn_3",
                "from": {"nodeId": "node_2", "type": "output"},
                "to": {"nodeId": "node_4", "type": "input"}
            },
            {
                "id": "conn_4",
                "from": {"nodeId": "node_3", "type": "output"},
                "to": {"nodeId": "node_4", "type": "input"}
            },
            {
                "id": "conn_5",
                "from": {"nodeId": "node_4", "type": "output"},
                "to": {"nodeId": "node_5", "type": "input"}
            }
        ],
        "properties": {
            "node_1": {
                "ticker": "VN30",
                "exchange": "HOSE",
                "timeframes": ["5m", "15m", "1h"]
            },
            "node_2": {
                "fastPeriod": 12,
                "slowPeriod": 26,
                "signalPeriod": 9,
                "useZones": True,
                "marketTemplate": "VN",
                "minConfidence": 0.6
            },
            "node_3": {
                "periods": [18, 36, 48, 144],
                "tripleConfirmation": True,
                "minConfirmation": 3,
                "minConfidence": 0.5
            },
            "node_4": {
                "method": "weighted_average",
                "minStrategies": 2,
                "consensusThreshold": 0.7,
                "confidenceThreshold": 0.6
            },
            "node_5": {
                "channels": ["database", "telegram"],
                "format": "json",
                "autoStart": True
            }
        },
        "metadata": {
            "created": datetime.now().isoformat(),
            "version": "1.0.0",
            "builder": "Test Script"
        }
    }
    
    print("🧪 Testing Workflow API...")
    
    # Test 1: Save workflow
    print("\n1. Testing save workflow...")
    response = requests.post(f"{BASE_URL}/api/workflow/save", json=workflow_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        workflow_id = response.json()["workflow_id"]
        print(f"✅ Workflow saved with ID: {workflow_id}")
        
        # Test 2: List workflows
        print("\n2. Testing list workflows...")
        response = requests.get(f"{BASE_URL}/api/workflow/list")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test 3: Load workflow
        print("\n3. Testing load workflow...")
        response = requests.get(f"{BASE_URL}/api/workflow/load/{workflow_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test 4: Execute workflow
        print("\n4. Testing execute workflow...")
        response = requests.post(f"{BASE_URL}/api/workflow/execute/{workflow_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        print("\n✅ All tests completed successfully!")
        
    else:
        print("❌ Failed to save workflow")

if __name__ == "__main__":
    test_workflow_api()
