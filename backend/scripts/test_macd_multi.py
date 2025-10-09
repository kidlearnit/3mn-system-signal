#!/usr/bin/env python3
"""
Test script for MACD Multi-TF functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from worker.macd_multi_jobs import job_macd_multi_pipeline
from app.db import SessionLocal

def test_macd_multi_pipeline():
    """Test MACD Multi-TF pipeline with sample data"""
    
    # Sample workflow configuration
    workflow_config = {
        'fastPeriod': 7,
        'slowPeriod': 113,
        'signalPeriod': 144,
        'symbolThresholds': [
            {
                'symbol': 'NVDA',
                'bubefsm2': 0.47,
                'bubefsm5': 0.47,
                'bubefsm15': 0.47,
                'bubefsm30': 0.47,
                'bubefs_1h': 1.74
            },
            {
                'symbol': 'MSFT',
                'bubefsm2': 1.74,
                'bubefsm5': 1.74,
                'bubefsm15': 1.74,
                'bubefsm30': 1.74,
                'bubefs_1h': 1.74
            }
        ]
    }
    
    # Get a test symbol from database
    with SessionLocal() as session:
        result = session.execute("""
            SELECT id, ticker, exchange 
            FROM symbols 
            WHERE active = 1 
            LIMIT 1
        """).fetchone()
        
        if not result:
            print("❌ No active symbols found in database")
            return
        
        symbol_id, ticker, exchange = result
        print(f"🧪 Testing MACD Multi-TF pipeline for {ticker} ({exchange})")
        
        # Execute pipeline
        result = job_macd_multi_pipeline(symbol_id, ticker, exchange, workflow_config)
        
        print(f"✅ Pipeline result: {result}")
        
        if isinstance(result, dict) and result.get('status') == 'success':
            print(f"📊 Overall signal: {result['overall_signal']['signal_type']}")
            print(f"🎯 Confidence: {result['overall_signal']['confidence']:.2f}")
            print(f"⏰ Timeframes processed: {len(result['timeframe_results'])}")
        else:
            print(f"⚠️ Pipeline returned: {result}")

def test_workflow_execution():
    """Test workflow execution with MACD Multi-TF node"""
    from worker.macd_multi_jobs import job_macd_multi_workflow_executor
    
    print("🧪 Testing MACD Multi-TF workflow executor")
    
    # Test with dummy workflow_id and node_id
    result = job_macd_multi_workflow_executor(1, "test-node-id")
    
    print(f"✅ Workflow executor result: {result}")

if __name__ == "__main__":
    print("🚀 Starting MACD Multi-TF tests...")
    
    try:
        test_macd_multi_pipeline()
        print("\n" + "="*50 + "\n")
        test_workflow_execution()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
