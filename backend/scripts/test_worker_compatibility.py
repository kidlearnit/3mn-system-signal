#!/usr/bin/env python3
"""
Test script to check if MACD Multi-TF US jobs can run in worker
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test all required imports"""
    print("🧪 Testing imports...")
    
    try:
        # Test basic imports
        import pandas as pd
        import numpy as np
        print("✅ Pandas, Numpy imported")
        
        # Test app imports
        from app.db import SessionLocal
        print("✅ Database imports")
        
        from app.services.logger import log_scheduler_info, log_scheduler_error
        from app.services.debug import debug_helper
        print("✅ Logger imports")
        
        from app.services.data_sources import fetch_latest_1m
        from app.services.candle_utils import load_candles_1m_df
        from app.services.resample import resample_ohlcv
        from app.services.indicators import compute_macd
        print("✅ Service imports")
        
        from app.models import Signal
        print("✅ Model imports")
        
        # Test worker imports
        from worker.macd_multi_us_jobs import job_macd_multi_us_pipeline
        print("✅ MACD Multi-TF US jobs imported")
        
        import worker.run_worker
        print("✅ Worker imports")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_worker_creation():
    """Test if worker can be created"""
    print("\n🧪 Testing worker creation...")
    
    try:
        import redis
        from rq import Worker, Queue, Connection
        
        # Test Redis connection
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        conn = redis.from_url(redis_url)
        
        # Test worker creation (without starting)
        with Connection(conn):
            worker = Worker(['default', 'priority'])
            print("✅ Worker created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Worker creation error: {e}")
        return False

def test_macd_multi_function():
    """Test MACD Multi-TF function with dummy data"""
    print("\n🧪 Testing MACD Multi-TF function...")
    
    try:
        from worker.macd_multi_us_jobs import job_macd_multi_us_pipeline
        
        # Dummy workflow config
        workflow_config = {
            'fastPeriod': 7,
            'slowPeriod': 113,
            'signalPeriod': 144,
            'symbolThresholds': [
                {
                    'symbol': 'TEST',
                    'bubefsm2': 0.47,
                    'bubefsm5': 0.47,
                    'bubefsm15': 0.47,
                    'bubefsm30': 0.47,
                    'bubefs_1h': 1.74
                }
            ]
        }
        
        # Test function call (will fail due to no data, but should not crash)
        result = job_macd_multi_us_pipeline(workflow_config, mode='realtime')
        print(f"✅ MACD Multi-TF function executed: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ MACD Multi-TF function error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_docker_requirements():
    """Test if Docker is required"""
    print("\n🧪 Testing Docker requirements...")
    
    try:
        # Check if we can connect to services
        import redis
        import pymysql
        
        # Test Redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        conn = redis.from_url(redis_url)
        conn.ping()
        print("✅ Redis connection successful")
        
        # Test MySQL (if available)
        try:
            from app.db import SessionLocal
            with SessionLocal() as session:
                session.execute("SELECT 1")
            print("✅ Database connection successful")
        except Exception as e:
            print(f"⚠️ Database connection failed: {e}")
            print("   This is expected if database is not running")
        
        return True
        
    except Exception as e:
        print(f"❌ Service connection error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing MACD Multi-TF US worker compatibility...")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_worker_creation,
        test_macd_multi_function,
        test_docker_requirements
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"✅ Passed: {sum(results)}/{len(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n🎉 All tests passed! MACD Multi-TF US jobs are ready to run in worker.")
        print("📋 Requirements:")
        print("   - Redis server running")
        print("   - MySQL database running")
        print("   - Python dependencies installed")
        print("   - Docker is NOT required for basic functionality")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
        print("💡 Docker may be required for full functionality.")
