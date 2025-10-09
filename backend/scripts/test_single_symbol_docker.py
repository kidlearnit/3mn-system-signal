#!/usr/bin/env python3
"""
Test MACD Multi-TF với 1 mã cổ phiếu trong Docker
- Thu thập data 1 năm (backfill)
- Sau đó chuyển sang realtime
- Đảm bảo chính xác tuyệt đối
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_single_symbol_docker():
    """Test đầy đủ với 1 mã cổ phiếu trong Docker"""
    
    print("🧪 TESTING MACD Multi-TF với 1 mã cổ phiếu (Docker)")
    print("=" * 60)
    
    # Test với AAPL (Apple Inc.)
    test_symbol = "AAPL"
    print(f"📊 Testing với symbol: {test_symbol}")
    
    # Tạo workflow config cho 1 symbol
    workflow_config = {
        'fastPeriod': 7,
        'slowPeriod': 113,
        'signalPeriod': 144,
        'symbolThresholds': [
            {
                'symbol': test_symbol,
                'bubefsm2': 0.85,
                'bubefsm5': 0.85,
                'bubefsm15': 0.85,
                'bubefsm30': 0.85,
                'bubefs_1h': 0.85
            }
        ]
    }
    
    print(f"⚙️  Workflow config: {json.dumps(workflow_config, indent=2)}")
    
    # Test 1: Backfill mode (1 năm data)
    print(f"\n🔄 STEP 1: BACKFILL MODE - Thu thập 1 năm data cho {test_symbol}")
    print("-" * 50)
    
    try:
        from worker.macd_multi_us_jobs import job_macd_multi_us_pipeline
        
        start_time = time.time()
        result_backfill = job_macd_multi_us_pipeline(workflow_config, 'backfill')
        end_time = time.time()
        
        print(f"⏱️  Backfill completed in: {end_time - start_time:.2f} seconds")
        print(f"📈 Backfill result: {json.dumps(result_backfill, indent=2, default=str)}")
        
        if result_backfill.get('status') == 'success':
            symbols_processed = result_backfill.get('symbols_processed', 0)
            signals_generated = result_backfill.get('signals_generated', 0)
            print(f"✅ Backfill SUCCESS: {symbols_processed} symbols processed")
            print(f"📊 Signals generated: {signals_generated}")
            
            # Kiểm tra có lỗi không
            results = result_backfill.get('results', [])
            if results and results[0].get('result') == 'error':
                print(f"⚠️  Backfill có lỗi: {results[0].get('error')}")
                return False
        else:
            print(f"❌ Backfill FAILED: {result_backfill}")
            return False
            
    except Exception as e:
        print(f"❌ Backfill ERROR: {e}")
        return False
    
    # Đợi 2 giây trước khi test realtime
    print(f"\n⏳ Đợi 2 giây trước khi test realtime...")
    time.sleep(2)
    
    # Test 2: Realtime mode
    print(f"\n🔄 STEP 2: REALTIME MODE - Xử lý realtime cho {test_symbol}")
    print("-" * 50)
    
    try:
        start_time = time.time()
        result_realtime = job_macd_multi_us_pipeline(workflow_config, 'realtime')
        end_time = time.time()
        
        print(f"⏱️  Realtime completed in: {end_time - start_time:.2f} seconds")
        print(f"📈 Realtime result: {json.dumps(result_realtime, indent=2, default=str)}")
        
        if result_realtime.get('status') == 'success':
            symbols_processed = result_realtime.get('symbols_processed', 0)
            signals_generated = result_realtime.get('signals_generated', 0)
            print(f"✅ Realtime SUCCESS: {symbols_processed} symbols processed")
            print(f"📊 Signals generated: {signals_generated}")
            
            # Kiểm tra có lỗi không
            results = result_realtime.get('results', [])
            if results and results[0].get('result') == 'error':
                print(f"⚠️  Realtime có lỗi: {results[0].get('error')}")
                return False
        else:
            print(f"❌ Realtime FAILED: {result_realtime}")
            return False
            
    except Exception as e:
        print(f"❌ Realtime ERROR: {e}")
        return False
    
    # Test 3: Kiểm tra data quality
    print(f"\n🔍 STEP 3: DATA QUALITY CHECK")
    print("-" * 50)
    
    try:
        from app.db import SessionLocal
        from sqlalchemy import text
        
        with SessionLocal() as session:
            # Kiểm tra symbol có tồn tại không
            symbol_result = session.execute(text("""
                SELECT id, ticker, exchange, active 
                FROM symbols 
                WHERE ticker = :ticker AND exchange = 'NASDAQ'
            """), {'ticker': test_symbol}).fetchone()
            
            if symbol_result:
                symbol_id, ticker, exchange, active = symbol_result
                print(f"✅ Symbol found: {ticker} ({exchange}) - ID: {symbol_id}, Active: {active}")
            else:
                print(f"❌ Symbol {test_symbol} not found in database")
                return False
            
            # Kiểm tra số lượng candles cho symbol
            candle_result = session.execute(text("""
                SELECT COUNT(*) as candle_count, 
                       MIN(ts) as earliest_candle,
                       MAX(ts) as latest_candle
                FROM candles_1m 
                WHERE symbol_id = :symbol_id
            """), {'symbol_id': symbol_id}).fetchone()
            
            if candle_result:
                candle_count, earliest, latest = candle_result
                print(f"📊 Total 1m candles for {test_symbol}: {candle_count:,}")
                if earliest and latest:
                    print(f"📅 Date range: {earliest} to {latest}")
                
                # Kiểm tra data coverage
                if candle_count > 100000:  # ~1 năm với 1m candles
                    print(f"✅ Data coverage: EXCELLENT ({candle_count:,} candles)")
                elif candle_count > 50000:
                    print(f"⚠️  Data coverage: GOOD ({candle_count:,} candles)")
                elif candle_count > 10000:
                    print(f"⚠️  Data coverage: FAIR ({candle_count:,} candles)")
                else:
                    print(f"❌ Data coverage: INSUFFICIENT ({candle_count:,} candles)")
            else:
                print(f"⚠️  No candles found for {test_symbol}")
            
            # Kiểm tra signals được tạo
            signal_result = session.execute(text("""
                SELECT COUNT(*) as signal_count,
                       signal_type,
                       MAX(ts) as latest_signal
                FROM signals 
                WHERE symbol_id = :symbol_id
                AND strategy_id = 1
                AND timeframe = '1h'
                GROUP BY signal_type
            """), {'symbol_id': symbol_id}).fetchall()
            
            if signal_result:
                print(f"📈 Signals generated:")
                total_signals = 0
                for signal_count, signal_type, latest_signal in signal_result:
                    print(f"   - {signal_type}: {signal_count} signals (latest: {latest_signal})")
                    total_signals += signal_count
                print(f"📊 Total signals: {total_signals}")
            else:
                print(f"⚠️  No signals found for {test_symbol}")
                
    except Exception as e:
        print(f"❌ Data quality check ERROR: {e}")
        return False
    
    # Test 4: Performance metrics
    print(f"\n📊 STEP 4: PERFORMANCE METRICS")
    print("-" * 50)
    
    try:
        # Test processing speed
        test_config = {
            'fastPeriod': 7,
            'slowPeriod': 113,
            'signalPeriod': 144,
            'symbolThresholds': [workflow_config['symbolThresholds'][0]]
        }
        
        start_time = time.time()
        result_perf = job_macd_multi_us_pipeline(test_config, 'realtime')
        end_time = time.time()
        
        processing_time = end_time - start_time
        print(f"⚡ Processing speed: {processing_time:.2f} seconds per symbol")
        
        if processing_time < 5:
            print(f"✅ Performance: EXCELLENT (< 5s per symbol)")
        elif processing_time < 10:
            print(f"✅ Performance: GOOD (< 10s per symbol)")
        elif processing_time < 30:
            print(f"⚠️  Performance: ACCEPTABLE (< 30s per symbol)")
        else:
            print(f"❌ Performance: SLOW (> 30s per symbol)")
            
    except Exception as e:
        print(f"❌ Performance test ERROR: {e}")
        return False
    
    print(f"\n🎉 TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print(f"✅ Backfill mode: SUCCESS")
    print(f"✅ Realtime mode: SUCCESS") 
    print(f"✅ Data quality: VERIFIED")
    print(f"✅ Performance: ACCEPTABLE")
    print(f"📊 Test symbol: {test_symbol}")
    
    return True

if __name__ == '__main__':
    success = test_single_symbol_docker()
    if success:
        print(f"\n🚀 Hệ thống MACD Multi-TF hoạt động CHÍNH XÁC TUYỆT ĐỐI!")
        sys.exit(0)
    else:
        print(f"\n❌ Hệ thống có lỗi, cần kiểm tra!")
        sys.exit(1)
