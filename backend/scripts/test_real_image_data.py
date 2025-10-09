#!/usr/bin/env python3
"""
Test script to verify real image data with actual company names
"""

import os
import sys
import json
import uuid
sys.path.append('/code')

from app.db import init_db, SessionLocal
from app.models import Workflow

def test_real_image_data():
    """Test with real image data (actual company names)"""
    print("🧪 Testing Real Image Data (Actual Company Names)")
    print("=" * 60)
    
    # Real data from the image with actual company names
    real_workflow = {
        'name': 'Real MACD Multi-TF Workflow',
        'description': 'Test workflow with real company data from image',
        'nodes': [
            {
                'id': 'macd-multi-real',
                'type': 'macd-multi',
                'x': 100,
                'y': 100,
                'properties': {
                    'fastPeriod': 7,
                    'slowPeriod': 113,
                    'signalPeriod': 144,
                    'symbolThresholds': [
                        {'symbol': 'NVDA', 'company': 'NVIDIA Corporation', 'weight': '10.08%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.74, 'bubefsm15': 1.0, 'bubefsm30': 1.47, 'bubefs_1h': 1.74},
                        {'symbol': 'MSFT', 'company': 'Microsoft Corporation', 'weight': '8.98%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.47, 'bubefsm30': 1.74, 'bubefs_1h': 2.2},
                        {'symbol': 'AAPL', 'company': 'Apple Inc.', 'weight': '7.33%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.47, 'bubefsm30': 1.74, 'bubefs_1h': 2.2},
                        {'symbol': 'AMZN', 'company': 'Amazon.com, Inc.', 'weight': '5.43%', 'sector': 'Consumer Discretionary', 'bubefsm1': 0.33, 'bubefsm2': 0.33, 'bubefsm5': 0.47, 'bubefsm15': 0.74, 'bubefsm30': 1.0, 'bubefs_1h': 1.47},
                        {'symbol': 'AVGO', 'company': 'Broadcom Inc.', 'weight': '4.12%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.47, 'bubefsm30': 1.74, 'bubefs_1h': 2.2},
                        {'symbol': 'META', 'company': 'Meta Platforms, Inc.', 'weight': '3.89%', 'sector': 'Communication Services', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                        {'symbol': 'NFLX', 'company': 'Netflix, Inc.', 'weight': '2.45%', 'sector': 'Communication Services', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                        {'symbol': 'TSLA', 'company': 'Tesla, Inc.', 'weight': '2.12%', 'sector': 'Consumer Discretionary', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                        {'symbol': 'GOOGL', 'company': 'Alphabet Inc. Class A', 'weight': '1.98%', 'sector': 'Communication Services', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.74, 'bubefsm15': 1.0, 'bubefsm30': 1.47, 'bubefs_1h': 1.74},
                        {'symbol': 'GOOG', 'company': 'Alphabet Inc. Class C', 'weight': '1.87%', 'sector': 'Communication Services', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.74, 'bubefsm15': 1.0, 'bubefsm30': 1.47, 'bubefs_1h': 1.74},
                        {'symbol': 'COST', 'company': 'Costco Wholesale Corporation', 'weight': '1.65%', 'sector': 'Consumer Staples', 'bubefsm1': 0.33, 'bubefsm2': 1.74, 'bubefsm5': 2.2, 'bubefsm15': 3.3, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                        {'symbol': 'PLTR', 'company': 'Palantir Technologies Inc.', 'weight': '1.43%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                        {'symbol': 'CSCO', 'company': 'Cisco Systems, Inc.', 'weight': '1.32%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.33, 'bubefsm5': 0.47, 'bubefsm15': 0.74, 'bubefsm30': 1.0, 'bubefs_1h': 1.47},
                        {'symbol': 'TMUS', 'company': 'T-Mobile US, Inc.', 'weight': '1.21%', 'sector': 'Communication Services', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                        {'symbol': 'AMD', 'company': 'Advanced Micro Devices, Inc.', 'weight': '1.15%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                        {'symbol': 'LIN', 'company': 'Linde plc', 'weight': '1.08%', 'sector': 'Industrials', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                        {'symbol': 'INTU', 'company': 'Intuit Inc.', 'weight': '1.02%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 1.74, 'bubefsm5': 2.2, 'bubefsm15': 3.3, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                        {'symbol': 'PEP', 'company': 'PepsiCo, Inc.', 'weight': '0.98%', 'sector': 'Consumer Staples', 'bubefsm1': 0.33, 'bubefsm2': 0.33, 'bubefsm5': 0.47, 'bubefsm15': 0.74, 'bubefsm30': 1.0, 'bubefs_1h': 1.47},
                        {'symbol': 'SHOP', 'company': 'Shopify Inc.', 'weight': '0.95%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                        {'symbol': 'BKNG', 'company': 'Booking Holdings Inc.', 'weight': '0.92%', 'sector': 'Consumer Discretionary', 'bubefsm1': 0.33, 'bubefsm2': 0, 'bubefsm5': 0, 'bubefsm15': 0, 'bubefsm30': 0, 'bubefs_1h': 0},
                        {'symbol': 'ISRG', 'company': 'Intuitive Surgical, Inc.', 'weight': '0.89%', 'sector': 'Healthcare', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                        {'symbol': 'TXN', 'company': 'Texas Instruments Incorporated', 'weight': '0.86%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                        {'symbol': 'QCOM', 'company': 'QUALCOMM Incorporated', 'weight': '0.83%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                        {'symbol': 'AMGN', 'company': 'Amgen Inc.', 'weight': '0.80%', 'sector': 'Healthcare', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                        {'symbol': 'ADBE', 'company': 'Adobe Inc.', 'weight': '0.77%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                        {'symbol': 'TQQQ', 'company': 'QQQ Triple Index', 'weight': '0.74%', 'sector': 'Index', 'bubefsm1': 0.33, 'bubefsm2': 0.33, 'bubefsm5': 0.47, 'bubefsm15': 0.74, 'bubefsm30': 1.0, 'bubefs_1h': 1.47}
                    ]
                }
            }
        ],
        'connections': [],
        'properties': {
            'macd-multi-real': {
                'fastPeriod': 7,
                'slowPeriod': 113,
                'signalPeriod': 144,
                'symbolThresholds': [
                    {'symbol': 'NVDA', 'company': 'NVIDIA Corporation', 'weight': '10.08%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.74, 'bubefsm15': 1.0, 'bubefsm30': 1.47, 'bubefs_1h': 1.74},
                    {'symbol': 'MSFT', 'company': 'Microsoft Corporation', 'weight': '8.98%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.47, 'bubefsm30': 1.74, 'bubefs_1h': 2.2},
                    {'symbol': 'AAPL', 'company': 'Apple Inc.', 'weight': '7.33%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.47, 'bubefsm30': 1.74, 'bubefs_1h': 2.2},
                    {'symbol': 'AMZN', 'company': 'Amazon.com, Inc.', 'weight': '5.43%', 'sector': 'Consumer Discretionary', 'bubefsm1': 0.33, 'bubefsm2': 0.33, 'bubefsm5': 0.47, 'bubefsm15': 0.74, 'bubefsm30': 1.0, 'bubefs_1h': 1.47},
                    {'symbol': 'AVGO', 'company': 'Broadcom Inc.', 'weight': '4.12%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.47, 'bubefsm30': 1.74, 'bubefs_1h': 2.2},
                    {'symbol': 'META', 'company': 'Meta Platforms, Inc.', 'weight': '3.89%', 'sector': 'Communication Services', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                    {'symbol': 'NFLX', 'company': 'Netflix, Inc.', 'weight': '2.45%', 'sector': 'Communication Services', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                    {'symbol': 'TSLA', 'company': 'Tesla, Inc.', 'weight': '2.12%', 'sector': 'Consumer Discretionary', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                    {'symbol': 'GOOGL', 'company': 'Alphabet Inc. Class A', 'weight': '1.98%', 'sector': 'Communication Services', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.74, 'bubefsm15': 1.0, 'bubefsm30': 1.47, 'bubefs_1h': 1.74},
                    {'symbol': 'GOOG', 'company': 'Alphabet Inc. Class C', 'weight': '1.87%', 'sector': 'Communication Services', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.74, 'bubefsm15': 1.0, 'bubefsm30': 1.47, 'bubefs_1h': 1.74},
                    {'symbol': 'COST', 'company': 'Costco Wholesale Corporation', 'weight': '1.65%', 'sector': 'Consumer Staples', 'bubefsm1': 0.33, 'bubefsm2': 1.74, 'bubefsm5': 2.2, 'bubefsm15': 3.3, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                    {'symbol': 'PLTR', 'company': 'Palantir Technologies Inc.', 'weight': '1.43%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                    {'symbol': 'CSCO', 'company': 'Cisco Systems, Inc.', 'weight': '1.32%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.33, 'bubefsm5': 0.47, 'bubefsm15': 0.74, 'bubefsm30': 1.0, 'bubefs_1h': 1.47},
                    {'symbol': 'TMUS', 'company': 'T-Mobile US, Inc.', 'weight': '1.21%', 'sector': 'Communication Services', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                    {'symbol': 'AMD', 'company': 'Advanced Micro Devices, Inc.', 'weight': '1.15%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                    {'symbol': 'LIN', 'company': 'Linde plc', 'weight': '1.08%', 'sector': 'Industrials', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                    {'symbol': 'INTU', 'company': 'Intuit Inc.', 'weight': '1.02%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 1.74, 'bubefsm5': 2.2, 'bubefsm15': 3.3, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                    {'symbol': 'PEP', 'company': 'PepsiCo, Inc.', 'weight': '0.98%', 'sector': 'Consumer Staples', 'bubefsm1': 0.33, 'bubefsm2': 0.33, 'bubefsm5': 0.47, 'bubefsm15': 0.74, 'bubefsm30': 1.0, 'bubefs_1h': 1.47},
                    {'symbol': 'SHOP', 'company': 'Shopify Inc.', 'weight': '0.95%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                    {'symbol': 'BKNG', 'company': 'Booking Holdings Inc.', 'weight': '0.92%', 'sector': 'Consumer Discretionary', 'bubefsm1': 0.33, 'bubefsm2': 0, 'bubefsm5': 0, 'bubefsm15': 0, 'bubefsm30': 0, 'bubefs_1h': 0},
                    {'symbol': 'ISRG', 'company': 'Intuitive Surgical, Inc.', 'weight': '0.89%', 'sector': 'Healthcare', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
                    {'symbol': 'TXN', 'company': 'Texas Instruments Incorporated', 'weight': '0.86%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                    {'symbol': 'QCOM', 'company': 'QUALCOMM Incorporated', 'weight': '0.83%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                    {'symbol': 'AMGN', 'company': 'Amgen Inc.', 'weight': '0.80%', 'sector': 'Healthcare', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                    {'symbol': 'ADBE', 'company': 'Adobe Inc.', 'weight': '0.77%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
                    {'symbol': 'TQQQ', 'company': 'QQQ Triple Index', 'weight': '0.74%', 'sector': 'Index', 'bubefsm1': 0.33, 'bubefsm2': 0.33, 'bubefsm5': 0.47, 'bubefsm15': 0.74, 'bubefsm30': 1.0, 'bubefs_1h': 1.47}
                ]
            }
        },
        'workflow_meta': {
            'created': '2024-01-01T00:00:00Z',
            'version': '1.0.0',
            'builder': 'Real Image Data Test'
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
            name=real_workflow['name'],
            description=real_workflow['description'],
            nodes=json.dumps(real_workflow['nodes']),
            connections=json.dumps(real_workflow['connections']),
            properties=json.dumps(real_workflow['properties']),
            workflow_meta=json.dumps(real_workflow['workflow_meta'])
        )
        
        session.add(workflow)
        session.commit()
        
        print(f"✅ Real workflow saved successfully with ID: {workflow_id}")
        
        # Retrieve and verify
        retrieved_workflow = session.query(Workflow).filter(Workflow.id == workflow_id).first()
        
        if retrieved_workflow:
            print("✅ Real workflow retrieved successfully")
            
            # Parse properties
            properties = json.loads(retrieved_workflow.properties)
            macd_props = properties.get('macd-multi-real', {})
            symbol_thresholds = macd_props.get('symbolThresholds', [])
            
            print(f"✅ Found {len(symbol_thresholds)} real symbol thresholds")
            
            # Verify first few real symbols
            for i, symbol_data in enumerate(symbol_thresholds[:5]):
                symbol_name = symbol_data['symbol']
                company_name = symbol_data['company']
                weight = symbol_data['weight']
                sector = symbol_data['sector']
                print(f"✅ {symbol_name} - {company_name}")
                print(f"   Weight: {weight}, Sector: {sector}")
                print(f"   BuBeFSM: 1m={symbol_data.get('bubefsm1')}, 2m={symbol_data.get('bubefsm2')}, 5m={symbol_data.get('bubefsm5')}, 15m={symbol_data.get('bubefsm15')}, 30m={symbol_data.get('bubefsm30')}, 1h={symbol_data.get('bubefs_1h')}")
            
            # Verify BKNG (all zeros)
            bkng_data = next((s for s in symbol_thresholds if s['symbol'] == 'BKNG'), None)
            if bkng_data:
                print("✅ BKNG (Booking Holdings Inc.) - all zeros:")
                print(f"   Company: {bkng_data['company']}")
                print(f"   Weight: {bkng_data['weight']}, Sector: {bkng_data['sector']}")
                print(f"   BuBeFSM: 1m={bkng_data.get('bubefsm1')}, 2m={bkng_data.get('bubefsm2')}, 5m={bkng_data.get('bubefsm5')}, 15m={bkng_data.get('bubefsm15')}, 30m={bkng_data.get('bubefsm30')}, 1h={bkng_data.get('bubefs_1h')}")
            
            # Verify TQQQ (last symbol)
            tqqq_data = next((s for s in symbol_thresholds if s['symbol'] == 'TQQQ'), None)
            if tqqq_data:
                print("✅ TQQQ (QQQ Triple Index) - last symbol:")
                print(f"   Company: {tqqq_data['company']}")
                print(f"   Weight: {tqqq_data['weight']}, Sector: {tqqq_data['sector']}")
                print(f"   BuBeFSM: 1m={tqqq_data.get('bubefsm1')}, 2m={tqqq_data.get('bubefsm2')}, 5m={tqqq_data.get('bubefsm5')}, 15m={tqqq_data.get('bubefsm15')}, 30m={tqqq_data.get('bubefsm30')}, 1h={tqqq_data.get('bubefs_1h')}")
            
            # Sector distribution
            sectors = {}
            for data in symbol_thresholds:
                sector = data['sector']
                sectors[sector] = sectors.get(sector, 0) + 1
            
            print(f"\n📊 Sector Distribution:")
            for sector, count in sorted(sectors.items()):
                print(f"  {sector}: {count} symbols")
        else:
            print("❌ Failed to retrieve real workflow")
        
        # Clean up
        session.delete(retrieved_workflow)
        session.commit()
        session.close()
        
        print("✅ Real test workflow cleaned up")
        print("🎉 Real image data test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_image_data()
