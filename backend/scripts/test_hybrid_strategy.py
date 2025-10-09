#!/usr/bin/env python3
"""
Test Hybrid Strategy - Kiểm tra hybrid strategy với dữ liệu thực
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text

# Add project root to path
sys.path.append('/code')

from app.db import SessionLocal, init_db
from app.services.hybrid_signal_engine import hybrid_signal_engine
from app.services.debug import debug_helper

# Initialize DB
if SessionLocal is None:
    init_db(os.getenv("DATABASE_URL"))

def test_hybrid_strategy():
    """Test hybrid strategy với dữ liệu thực"""
    
    print("🎯 Testing Hybrid Strategy (SMA + MACD)")
    print("=" * 50)
    
    try:
        with SessionLocal() as s:
            # Lấy danh sách symbols có dữ liệu
            symbols_query = """
                SELECT DISTINCT s.id, s.ticker, s.exchange
                FROM symbols s
                WHERE EXISTS (
                    SELECT 1 FROM indicators_sma sma 
                    WHERE sma.symbol_id = s.id
                ) AND EXISTS (
                    SELECT 1 FROM indicators_macd macd 
                    WHERE macd.symbol_id = s.id
                )
                LIMIT 5
            """
            
            symbols = s.execute(text(symbols_query)).fetchall()
            
            if not symbols:
                print("❌ No symbols with both SMA and MACD data found")
                return False
            
            print(f"📊 Found {len(symbols)} symbols with data")
            
            for symbol in symbols:
                symbol_id, ticker, exchange = symbol
                print(f"\n🔍 Testing {ticker} ({exchange})")
                print("-" * 30)
                
                # Test single timeframe
                test_single_timeframe(symbol_id, ticker, exchange, '5m')
                
                # Test multi-timeframe
                test_multi_timeframe(symbol_id, ticker, exchange)
                
                print()
            
            return True
            
    except Exception as e:
        print(f"❌ Error testing hybrid strategy: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_single_timeframe(symbol_id: int, ticker: str, exchange: str, timeframe: str):
    """Test hybrid signal cho một timeframe"""
    
    try:
        print(f"  📈 Testing {timeframe} timeframe...")
        
        # Đánh giá tín hiệu hybrid
        result = hybrid_signal_engine.evaluate_hybrid_signal(
            symbol_id, ticker, exchange, timeframe
        )
        
        if result.get('error'):
            print(f"    ❌ Error: {result.get('error')}")
            return
        
        # Hiển thị kết quả
        hybrid_signal = result.get('hybrid_signal', 'N/A')
        hybrid_direction = result.get('hybrid_direction', 'N/A')
        hybrid_strength = result.get('hybrid_strength', 0.0)
        confidence = result.get('confidence', 0.0)
        
        sma_signal = result.get('sma_signal', {})
        macd_signal = result.get('macd_signal', {})
        
        print(f"    🎯 Hybrid Signal: {hybrid_signal}")
        print(f"    📊 Direction: {hybrid_direction}")
        print(f"    💪 Strength: {hybrid_strength:.2f}")
        print(f"    🎯 Confidence: {confidence:.2f}")
        print(f"    📈 SMA: {sma_signal.get('signal_type', 'N/A')} ({sma_signal.get('direction', 'N/A')})")
        print(f"    📊 MACD: {macd_signal.get('signal_type', 'N/A')} ({macd_signal.get('direction', 'N/A')})")
        
        # Đánh giá chất lượng tín hiệu
        if confidence > 0.8:
            print(f"    ✅ High confidence signal!")
        elif confidence > 0.6:
            print(f"    ⚠️ Medium confidence signal")
        else:
            print(f"    ❌ Low confidence signal")
            
    except Exception as e:
        print(f"    ❌ Error testing {timeframe}: {e}")

def test_multi_timeframe(symbol_id: int, ticker: str, exchange: str):
    """Test hybrid signal cho nhiều timeframes"""
    
    try:
        print(f"  🔄 Testing multi-timeframe analysis...")
        
        # Đánh giá tín hiệu multi-timeframe
        result = hybrid_signal_engine.evaluate_multi_timeframe_hybrid(
            symbol_id, ticker, exchange
        )
        
        if result.get('error'):
            print(f"    ❌ Error: {result.get('error')}")
            return
        
        # Hiển thị kết quả tổng thể
        overall_direction = result.get('overall_direction', 'N/A')
        overall_strength = result.get('overall_strength', 0.0)
        overall_confidence = result.get('overall_confidence', 0.0)
        buy_ratio = result.get('buy_ratio', 0.0)
        sell_ratio = result.get('sell_ratio', 0.0)
        
        print(f"    🎯 Overall Direction: {overall_direction}")
        print(f"    💪 Overall Strength: {overall_strength:.2f}")
        print(f"    🎯 Overall Confidence: {overall_confidence:.2f}")
        print(f"    📈 Buy Ratio: {buy_ratio:.2f}")
        print(f"    📉 Sell Ratio: {sell_ratio:.2f}")
        
        # Hiển thị chi tiết từng timeframe
        timeframe_results = result.get('timeframe_results', {})
        print(f"    📊 Timeframe Details:")
        
        for tf, tf_result in timeframe_results.items():
            if tf_result.get('error'):
                continue
                
            signal = tf_result.get('hybrid_signal', 'N/A')
            direction = tf_result.get('hybrid_direction', 'N/A')
            confidence = tf_result.get('confidence', 0.0)
            
            print(f"      {tf}: {direction} ({confidence:.2f})")
        
        # Đánh giá chất lượng tín hiệu tổng thể
        if overall_confidence > 0.8:
            print(f"    ✅ Strong multi-timeframe signal!")
        elif overall_confidence > 0.6:
            print(f"    ⚠️ Moderate multi-timeframe signal")
        else:
            print(f"    ❌ Weak multi-timeframe signal")
            
    except Exception as e:
        print(f"    ❌ Error testing multi-timeframe: {e}")

def test_hybrid_performance():
    """Test hiệu suất của hybrid strategy"""
    
    print("\n📊 Testing Hybrid Strategy Performance")
    print("=" * 50)
    
    try:
        with SessionLocal() as s:
            # Thống kê tín hiệu trong 24h qua
            stats_query = """
                SELECT 
                    COUNT(*) as total_signals,
                    AVG(confidence) as avg_confidence,
                    AVG(hybrid_strength) as avg_strength,
                    SUM(CASE WHEN hybrid_direction = 'BUY' THEN 1 ELSE 0 END) as buy_signals,
                    SUM(CASE WHEN hybrid_direction = 'SELL' THEN 1 ELSE 0 END) as sell_signals,
                    SUM(CASE WHEN hybrid_direction = 'NEUTRAL' THEN 1 ELSE 0 END) as neutral_signals
                FROM hybrid_signals
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """
            
            stats = s.execute(text(stats_query)).first()
            
            if stats.total_signals == 0:
                print("❌ No hybrid signals found in the last 24 hours")
                return
            
            print(f"📈 Total Signals (24h): {stats.total_signals}")
            print(f"🎯 Average Confidence: {stats.avg_confidence:.2f}")
            print(f"💪 Average Strength: {stats.avg_strength:.2f}")
            print(f"📈 Buy Signals: {stats.buy_signals}")
            print(f"📉 Sell Signals: {stats.sell_signals}")
            print(f"⚪ Neutral Signals: {stats.neutral_signals}")
            
            # Thống kê theo timeframe
            tf_query = """
                SELECT 
                    timeframe,
                    COUNT(*) as count,
                    AVG(confidence) as avg_confidence
                FROM hybrid_signals
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                GROUP BY timeframe
                ORDER BY count DESC
            """
            
            tf_stats = s.execute(text(tf_query)).fetchall()
            
            print(f"\n📊 Signals by Timeframe:")
            for tf_stat in tf_stats:
                print(f"  {tf_stat.timeframe}: {tf_stat.count} signals (avg confidence: {tf_stat.avg_confidence:.2f})")
            
            return True
            
    except Exception as e:
        print(f"❌ Error testing performance: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Starting Hybrid Strategy Test")
    print("=" * 60)
    
    try:
        # Test hybrid strategy
        success = test_hybrid_strategy()
        
        if success:
            # Test performance
            test_hybrid_performance()
            
            print("\n✅ Hybrid Strategy Test Completed Successfully!")
            print("💡 The hybrid strategy is working correctly")
        else:
            print("\n❌ Hybrid Strategy Test Failed!")
            print("💡 Check the logs for more details")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
