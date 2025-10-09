#!/usr/bin/env python3
"""
Test script to verify workflow save functionality
"""

import os
import sys
import json
import uuid
sys.path.append('/code')

from app.db import init_db, SessionLocal
from app.models import Workflow

def test_workflow_save():
    """Test workflow save functionality"""
    print("🧪 Testing Workflow Save Functionality")
    print("=" * 50)
    
    # Initialize database
    init_db(os.getenv("DATABASE_URL"))
    
    # Create a test workflow
    test_workflow = {
        'name': 'Test MACD Multi-TF Workflow',
        'description': 'Test workflow for MACD Multi-TF configuration',
        'nodes': [
            {
                'id': 'node1',
                'type': 'macd-multi',
                'x': 100,
                'y': 100,
                'properties': {
                    'fastPeriod': 7,
                    'slowPeriod': 113,
                    'signalPeriod': 144,
                    'symbolThresholds': [
                        {
                            'symbol': 'NVDA',
                            'bubefsm1': 0.33,
                            'bubefsm2': 0.47,
                            'bubefsm5': 0.74,
                            'bubefsm15': 1.0,
                            'bubefsm30': 1.47,
                            'bubefs_1h': 1.74
                        },
                        {
                            'symbol': 'MSFT',
                            'bubefsm1': 0.33,
                            'bubefsm2': 0.74,
                            'bubefsm5': 1.0,
                            'bubefsm15': 1.47,
                            'bubefsm30': 1.74,
                            'bubefs_1h': 2.2
                        }
                    ]
                }
            }
        ],
        'connections': [],
        'properties': {
            'node1': {
                'fastPeriod': 7,
                'slowPeriod': 113,
                'signalPeriod': 144,
                'symbolThresholds': [
                    {
                        'symbol': 'NVDA',
                        'bubefsm1': 0.33,
                        'bubefsm2': 0.47,
                        'bubefsm5': 0.74,
                        'bubefsm15': 1.0,
                        'bubefsm30': 1.47,
                        'bubefs_1h': 1.74
                    },
                    {
                        'symbol': 'MSFT',
                        'bubefsm1': 0.33,
                        'bubefsm2': 0.74,
                        'bubefsm5': 1.0,
                        'bubefsm15': 1.47,
                        'bubefsm30': 1.74,
                        'bubefs_1h': 2.2
                    }
                ]
            }
        },
        'metadata': {
            'created': '2024-01-01T00:00:00Z',
            'version': '1.0.0',
            'builder': 'Test Script'
        }
    }
    
    try:
        # Initialize database
        init_db(os.getenv("DATABASE_URL"))
        
        # Re-import SessionLocal after init_db
        from app.db import SessionLocal
        
        # Save workflow
        session = SessionLocal()
        
        # Create workflow object
        workflow_id = str(uuid.uuid4())
        workflow = Workflow(
            id=workflow_id,
            name=test_workflow['name'],
            description=test_workflow['description'],
            nodes=json.dumps(test_workflow['nodes']),
            connections=json.dumps(test_workflow['connections']),
            properties=json.dumps(test_workflow['properties']),
            workflow_meta=json.dumps(test_workflow['metadata'])
        )
        
        session.add(workflow)
        session.commit()
        
        print(f"✅ Workflow saved successfully with ID: {workflow_id}")
        
        # Retrieve and verify
        retrieved_workflow = session.query(Workflow).filter(Workflow.id == workflow_id).first()
        
        if retrieved_workflow:
            print("✅ Workflow retrieved successfully")
            
            # Parse properties
            properties = json.loads(retrieved_workflow.properties)
            node1_props = properties.get('node1', {})
            symbol_thresholds = node1_props.get('symbolThresholds', [])
            
            print(f"✅ Found {len(symbol_thresholds)} symbol thresholds")
            
            # Verify NVDA data
            nvda_data = next((s for s in symbol_thresholds if s['symbol'] == 'NVDA'), None)
            if nvda_data:
                print("✅ NVDA data found:")
                print(f"   bubefsm1: {nvda_data.get('bubefsm1')}")
                print(f"   bubefsm2: {nvda_data.get('bubefsm2')}")
                print(f"   bubefsm5: {nvda_data.get('bubefsm5')}")
                print(f"   bubefsm15: {nvda_data.get('bubefsm15')}")
                print(f"   bubefsm30: {nvda_data.get('bubefsm30')}")
                print(f"   bubefs_1h: {nvda_data.get('bubefs_1h')}")
            else:
                print("❌ NVDA data not found")
            
            # Verify MSFT data
            msft_data = next((s for s in symbol_thresholds if s['symbol'] == 'MSFT'), None)
            if msft_data:
                print("✅ MSFT data found:")
                print(f"   bubefsm1: {msft_data.get('bubefsm1')}")
                print(f"   bubefsm2: {msft_data.get('bubefsm2')}")
                print(f"   bubefsm5: {msft_data.get('bubefsm5')}")
                print(f"   bubefsm15: {msft_data.get('bubefsm15')}")
                print(f"   bubefsm30: {msft_data.get('bubefsm30')}")
                print(f"   bubefs_1h: {msft_data.get('bubefs_1h')}")
            else:
                print("❌ MSFT data not found")
        else:
            print("❌ Failed to retrieve workflow")
        
        # Clean up
        session.delete(retrieved_workflow)
        session.commit()
        session.close()
        
        print("✅ Test workflow cleaned up")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_workflow_save()
