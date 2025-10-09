#!/usr/bin/env python3
"""
Test script to verify workflow error fixes
"""

import requests
import json
import uuid
from datetime import datetime

BASE_URL = "http://localhost:5010"

def test_workflow_error_fixes():
    """Test workflow API with various edge cases"""
    
    print("🧪 Testing Workflow Error Fixes...")
    
    # Test 1: Save workflow with minimal data
    print("\n1. Testing save workflow with minimal data...")
    minimal_workflow = {
        "name": "Minimal Test Workflow",
        "description": "Test with minimal data",
        "nodes": [],
        "connections": [],
        "properties": {},
        "metadata": {
            "created": datetime.now().isoformat(),
            "version": "1.0.0",
            "builder": "Test Script"
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/workflow/save", json=minimal_workflow)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {result}")
        
        if response.status_code == 200 and result.get('success'):
            workflow_id = result['workflow_id']
            print(f"✅ Minimal workflow saved with ID: {workflow_id}")
            
            # Test 2: Load the minimal workflow
            print("\n2. Testing load minimal workflow...")
            load_response = requests.get(f"{BASE_URL}/api/workflow/load/{workflow_id}")
            print(f"Status: {load_response.status_code}")
            load_result = load_response.json()
            print(f"Response: {load_result}")
            
            if load_response.status_code == 200 and load_result.get('success'):
                print("✅ Minimal workflow loaded successfully")
                
                # Test 3: Execute the minimal workflow
                print("\n3. Testing execute minimal workflow...")
                execute_response = requests.post(f"{BASE_URL}/api/workflow/execute/{workflow_id}")
                print(f"Status: {execute_response.status_code}")
                execute_result = execute_response.json()
                print(f"Response: {execute_result}")
                
                if execute_response.status_code == 200 and execute_result.get('success'):
                    print("✅ Minimal workflow executed successfully")
                else:
                    print("❌ Minimal workflow execution failed")
            else:
                print("❌ Minimal workflow load failed")
        else:
            print("❌ Minimal workflow save failed")
            
    except Exception as e:
        print(f"❌ Error testing minimal workflow: {e}")
    
    # Test 4: Save workflow with null/undefined values
    print("\n4. Testing save workflow with null values...")
    null_workflow = {
        "name": "Null Test Workflow",
        "description": "Test with null values",
        "nodes": None,
        "connections": None,
        "properties": None,
        "metadata": {
            "created": datetime.now().isoformat(),
            "version": "1.0.0",
            "builder": "Test Script"
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/workflow/save", json=null_workflow)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {result}")
        
        if response.status_code == 200 and result.get('success'):
            print("✅ Null workflow saved successfully")
        else:
            print("❌ Null workflow save failed (expected)")
            
    except Exception as e:
        print(f"❌ Error testing null workflow: {e}")
    
    # Test 5: List workflows
    print("\n5. Testing list workflows...")
    try:
        response = requests.get(f"{BASE_URL}/api/workflow/list")
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {result}")
        
        if response.status_code == 200 and result.get('success'):
            print(f"✅ Workflows listed successfully: {len(result.get('workflows', []))} workflows found")
        else:
            print("❌ List workflows failed")
            
    except Exception as e:
        print(f"❌ Error listing workflows: {e}")
    
    print("\n🎯 Error fix testing completed!")

if __name__ == "__main__":
    test_workflow_error_fixes()
