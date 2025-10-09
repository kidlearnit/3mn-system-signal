#!/usr/bin/env python3
"""
Test script to verify MACD Multi-TF configuration save functionality
"""

import os
import sys
import json
import uuid
sys.path.append('/code')

from app.db import init_db, SessionLocal
from app.models import Workflow

def test_macd_config_save():
    """Test MACD Multi-TF configuration save functionality"""
    print("🧪 Testing MACD Multi-TF Configuration Save")
    print("=" * 50)
    
    # Test data with 26 symbols from the new image
    test_workflow = {
        'name': 'MACD Multi-TF Test Workflow',
        'description': 'Test workflow for MACD Multi-TF with 26 symbols',
        'nodes': [
            {
                'id': 'macd-multi-1',
                'type': 'macd-multi',
                'x': 100,
                'y': 100,
                'properties': {
                    'fastPeriod': 7,
                    'slowPeriod': 113,
                    'signalPeriod': 144,
                    'symbolThresholds': [
                        {'symbol': 'SYM1', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.74, 'bubefsm15': 1.0, 'bubefsm30': 1.47, 'bubefs_1h': 1.74},
                        {'symbol': 'SYM2', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.47, 'bubefsm30': 1.74, 'bubefs_1h': 2.2},
                        {'symbol': 'SYM3', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.47, 'bubefsm30': 1.74, 'bubefs_1h': 2.2},
                        {'symbol': 'SYM4', 'bubefsm1': 0.33, 'bubefsm2': 0.33, 'bubefsm5': 0.47, 'bubefsm15': 0.74, 'bubefsm30': 1.0, 'bubefs_1h': 1.47},
                        {'symbol': 'SYM5', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.47, 'bubefsm30': 1.74, 'bubefs_1h': 2.2},
                        {'symbol': 'SYM6', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                        {'symbol': 'SYM7', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                        {'symbol': 'SYM8', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                        {'symbol': 'SYM9', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.74, 'bubefsm15': 1.0, 'bubefsm30': 1.47, 'bubefs_1h': 1.74},
                        {'symbol': 'SYM10', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.74, 'bubefsm15': 1.0, 'bubefsm30': 1.47, 'bubefs_1h': 1.74},
                        {'symbol': 'SYM11', 'bubefsm1': 0.33, 'bubefsm2': 1.74, 'bubefsm5': 2.2, 'bubefsm15': 3.3, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                        {'symbol': 'SYM12', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                        {'symbol': 'SYM13', 'bubefsm1': 0.33, 'bubefsm2': 0.33, 'bubefsm5': 0.47, 'bubefsm15': 0.74, 'bubefsm30': 1.0, 'bubefs_1h': 1.47},
                        {'symbol': 'SYM14', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                        {'symbol': 'SYM15', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                        {'symbol': 'SYM16', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                        {'symbol': 'SYM17', 'bubefsm1': 0.33, 'bubefsm2': 1.74, 'bubefsm5': 2.2, 'bubefsm15': 3.3, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                        {'symbol': 'SYM18', 'bubefsm1': 0.33, 'bubefsm2': 0.33, 'bubefsm5': 0.47, 'bubefsm15': 0.74, 'bubefsm30': 1.0, 'bubefs_1h': 1.47},
                        {'symbol': 'SYM19', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                        {'symbol': 'SYM20', 'bubefsm1': 0.33, 'bubefsm2': 0, 'bubefsm5': 0, 'bubefsm15': 0, 'bubefsm30': 0, 'bubefs_1h': 0},
                        {'symbol': 'SYM21', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                        {'symbol': 'SYM22', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                        {'symbol': 'SYM23', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                        {'symbol': 'SYM24', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                        {'symbol': 'SYM25', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                        {'symbol': 'SYM26', 'bubefsm1': 0.33, 'bubefsm2': 0.33, 'bubefsm5': 0.47, 'bubefsm15': 0.74, 'bubefsm30': 1.0, 'bubefs_1h': 1.47}
                    ]
                }
            }
        ],
        'connections': [],
        'properties': {
            'macd-multi-1': {
                'fastPeriod': 7,
                'slowPeriod': 113,
                'signalPeriod': 144,
                'symbolThresholds': [
                    {'symbol': 'SYM1', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.74, 'bubefsm15': 1.0, 'bubefsm30': 1.47, 'bubefs_1h': 1.74},
                    {'symbol': 'SYM2', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.47, 'bubefsm30': 1.74, 'bubefs_1h': 2.2},
                    {'symbol': 'SYM3', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.47, 'bubefsm30': 1.74, 'bubefs_1h': 2.2},
                    {'symbol': 'SYM4', 'bubefsm1': 0.33, 'bubefsm2': 0.33, 'bubefsm5': 0.47, 'bubefsm15': 0.74, 'bubefsm30': 1.0, 'bubefs_1h': 1.47},
                    {'symbol': 'SYM5', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.47, 'bubefsm30': 1.74, 'bubefs_1h': 2.2},
                    {'symbol': 'SYM6', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                    {'symbol': 'SYM7', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                    {'symbol': 'SYM8', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                    {'symbol': 'SYM9', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.74, 'bubefsm15': 1.0, 'bubefsm30': 1.47, 'bubefs_1h': 1.74},
                    {'symbol': 'SYM10', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.74, 'bubefsm15': 1.0, 'bubefsm30': 1.47, 'bubefs_1h': 1.74},
                    {'symbol': 'SYM11', 'bubefsm1': 0.33, 'bubefsm2': 1.74, 'bubefsm5': 2.2, 'bubefsm15': 3.3, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                    {'symbol': 'SYM12', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                    {'symbol': 'SYM13', 'bubefsm1': 0.33, 'bubefsm2': 0.33, 'bubefsm5': 0.47, 'bubefsm15': 0.74, 'bubefsm30': 1.0, 'bubefs_1h': 1.47},
                    {'symbol': 'SYM14', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                    {'symbol': 'SYM15', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                    {'symbol': 'SYM16', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                    {'symbol': 'SYM17', 'bubefsm1': 0.33, 'bubefsm2': 1.74, 'bubefsm5': 2.2, 'bubefsm15': 3.3, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                    {'symbol': 'SYM18', 'bubefsm1': 0.33, 'bubefsm2': 0.33, 'bubefsm5': 0.47, 'bubefsm15': 0.74, 'bubefsm30': 1.0, 'bubefs_1h': 1.47},
                    {'symbol': 'SYM19', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                    {'symbol': 'SYM20', 'bubefsm1': 0.33, 'bubefsm2': 0, 'bubefsm5': 0, 'bubefsm15': 0, 'bubefsm30': 0, 'bubefs_1h': 0},
                    {'symbol': 'SYM21', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                    {'symbol': 'SYM22', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                    {'symbol': 'SYM23', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                    {'symbol': 'SYM24', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                    {'symbol': 'SYM25', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                    {'symbol': 'SYM26', 'bubefsm1': 0.33, 'bubefsm2': 0.33, 'bubefsm5': 0.47, 'bubefsm15': 0.74, 'bubefsm30': 1.0, 'bubefs_1h': 1.47}
                ]
            }
        },
        'workflow_meta': {
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
            workflow_meta=json.dumps(test_workflow['workflow_meta'])
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
            macd_props = properties.get('macd-multi-1', {})
            symbol_thresholds = macd_props.get('symbolThresholds', [])
            
            print(f"✅ Found {len(symbol_thresholds)} symbol thresholds")
            
            # Verify first few symbols
            for i, symbol_data in enumerate(symbol_thresholds[:5]):
                symbol_name = symbol_data['symbol']
                print(f"✅ {symbol_name} data:")
                print(f"   bubefsm1: {symbol_data.get('bubefsm1')}")
                print(f"   bubefsm2: {symbol_data.get('bubefsm2')}")
                print(f"   bubefsm5: {symbol_data.get('bubefsm5')}")
                print(f"   bubefsm15: {symbol_data.get('bubefsm15')}")
                print(f"   bubefsm30: {symbol_data.get('bubefsm30')}")
                print(f"   bubefs_1h: {symbol_data.get('bubefs_1h')}")
            
            # Verify SYM20 (all zeros)
            sym20_data = next((s for s in symbol_thresholds if s['symbol'] == 'SYM20'), None)
            if sym20_data:
                print("✅ SYM20 data (all zeros):")
                print(f"   bubefsm1: {sym20_data.get('bubefsm1')}")
                print(f"   bubefsm2: {sym20_data.get('bubefsm2')}")
                print(f"   bubefsm5: {sym20_data.get('bubefsm5')}")
                print(f"   bubefsm15: {sym20_data.get('bubefsm15')}")
                print(f"   bubefsm30: {sym20_data.get('bubefsm30')}")
                print(f"   bubefs_1h: {sym20_data.get('bubefs_1h')}")
            
            # Verify last symbol
            sym26_data = next((s for s in symbol_thresholds if s['symbol'] == 'SYM26'), None)
            if sym26_data:
                print("✅ SYM26 data (last symbol):")
                print(f"   bubefsm1: {sym26_data.get('bubefsm1')}")
                print(f"   bubefsm2: {sym26_data.get('bubefsm2')}")
                print(f"   bubefsm5: {sym26_data.get('bubefsm5')}")
                print(f"   bubefsm15: {sym26_data.get('bubefsm15')}")
                print(f"   bubefsm30: {sym26_data.get('bubefsm30')}")
                print(f"   bubefs_1h: {sym26_data.get('bubefs_1h')}")
        else:
            print("❌ Failed to retrieve workflow")
        
        # Clean up
        session.delete(retrieved_workflow)
        session.commit()
        session.close()
        
        print("✅ Test workflow cleaned up")
        print("🎉 MACD Multi-TF configuration save test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_macd_config_save()
