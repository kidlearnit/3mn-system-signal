#!/usr/bin/env python3
"""
Test script cho VN Multi-Timeframe Strategy
Kết hợp MACD và MA across 7 timeframes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vn_multi_timeframe_strategy import VNMultiTimeframeEngine
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Get database connection"""
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "mysql"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "trader"),
        password=os.getenv("MYSQL_PASSWORD", "traderpass"),
        database=os.getenv("MYSQL_DATABASE", "trading_signals"),
        charset='utf8mb4'
    )
import json
from datetime import datetime

def test_vn_multi_timeframe_strategy():
    """Test VN Multi-Timeframe Strategy"""
    print("🚀 Testing VN Multi-Timeframe Strategy (MACD + MA 7 timeframes)")
    print("=" * 70)
    
    # Khởi tạo engine
    engine = VNMultiTimeframeEngine()
    
    # Lấy danh sách symbols VN
    print("\n📊 Getting VN symbols...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Lấy symbols VN
        cursor.execute("""
            SELECT id, ticker, exchange 
            FROM symbols 
            WHERE exchange = 'VN' 
            ORDER BY ticker 
            LIMIT 5
        """)
        
        vn_symbols = cursor.fetchall()
        
        if not vn_symbols:
            print("❌ No VN symbols found in database")
            return
        
        print(f"✅ Found {len(vn_symbols)} VN symbols:")
        for symbol in vn_symbols:
            print(f"   - {symbol[1]} ({symbol[2]}) - ID: {symbol[0]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error getting VN symbols: {e}")
        return
    
    # Test với symbol đầu tiên
    test_symbol = vn_symbols[0]
    symbol_id = test_symbol[0]
    symbol_ticker = test_symbol[1]
    
    print(f"\n🎯 Testing with symbol: {symbol_ticker} (ID: {symbol_id})")
    print("-" * 50)
    
    # Đánh giá multi-timeframe
    print("🔄 Evaluating multi-timeframe signals...")
    try:
        results = engine.evaluate_multi_timeframe(symbol_id)
        
        if "error" in results:
            print(f"❌ Error: {results['error']}")
            return
        
        # Hiển thị kết quả
        print("\n📈 Multi-Timeframe Results:")
        print("=" * 50)
        
        # Aggregated signal
        aggregated = results["aggregated_signal"]
        print(f"\n🎯 FINAL SIGNAL:")
        print(f"   Direction: {aggregated['direction']}")
        print(f"   Strength: {aggregated['strength']:.3f}")
        print(f"   Confidence: {aggregated['confidence']:.3f}")
        
        # Breakdown by timeframe
        print(f"\n📊 Timeframe Breakdown:")
        for tf, breakdown in aggregated["timeframe_breakdown"].items():
            macd_dir = breakdown["macd_direction"]
            ma_dir = breakdown["ma_direction"]
            weight = breakdown["weight"]
            
            # Color coding
            macd_color = "🟢" if macd_dir == "BUY" else "🔴" if macd_dir == "SELL" else "⚪"
            ma_color = "🟢" if ma_dir == "BUY" else "🔴" if ma_dir == "SELL" else "⚪"
            
            print(f"   {tf:>4}: MACD {macd_color} {macd_dir:>4} | MA {ma_color} {ma_dir:>4} | Weight: {weight:.1%}")
        
        # Detailed results
        print(f"\n🔍 Detailed Results:")
        for tf, tf_results in results["timeframe_results"].items():
            print(f"\n   📅 {tf} Timeframe:")
            
            # MACD details
            macd = tf_results["macd"]
            print(f"      MACD: {macd['direction']} (Strength: {macd['strength']:.3f}, Confidence: {macd['confidence']:.3f})")
            if "signal_type" in macd["details"]:
                print(f"             Signal Type: {macd['details']['signal_type']}")
            
            # MA details
            ma = tf_results["ma"]
            print(f"      MA:   {ma['direction']} (Strength: {ma['strength']:.3f}, Confidence: {ma['confidence']:.3f})")
            if "signal_type" in ma["details"]:
                print(f"             Signal Type: {ma['details']['signal_type']}")
        
        # Weights breakdown
        print(f"\n⚖️  Weight Analysis:")
        print(f"   MACD Buy Weight: {aggregated['macd_buy_weight']:.3f}")
        print(f"   MACD Sell Weight: {aggregated['macd_sell_weight']:.3f}")
        print(f"   MA Buy Weight: {aggregated['ma_buy_weight']:.3f}")
        print(f"   MA Sell Weight: {aggregated['ma_sell_weight']:.3f}")
        print(f"   Total Buy Weight: {aggregated['total_buy_weight']:.3f}")
        print(f"   Total Sell Weight: {aggregated['total_sell_weight']:.3f}")
        
        # Trading recommendation
        print(f"\n💡 Trading Recommendation:")
        if aggregated['direction'] == 'BUY' and aggregated['confidence'] > 0.6:
            print(f"   🟢 STRONG BUY - High confidence signal")
        elif aggregated['direction'] == 'BUY' and aggregated['confidence'] > 0.4:
            print(f"   🟡 WEAK BUY - Moderate confidence signal")
        elif aggregated['direction'] == 'SELL' and aggregated['confidence'] > 0.6:
            print(f"   🔴 STRONG SELL - High confidence signal")
        elif aggregated['direction'] == 'SELL' and aggregated['confidence'] > 0.4:
            print(f"   🟠 WEAK SELL - Moderate confidence signal")
        else:
            print(f"   ⚪ NEUTRAL - Low confidence or mixed signals")
        
        # Save results to file
        output_file = f"vn_multi_timeframe_results_{symbol_ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error evaluating multi-timeframe: {e}")
        import traceback
        traceback.print_exc()

def test_individual_strategies():
    """Test individual strategies"""
    print("\n🧪 Testing Individual Strategies")
    print("=" * 50)
    
    from app.services.vn_multi_timeframe_strategy import VNMultiTimeframeMACDStrategy, VNMultiTimeframeMAStrategy
    from app.services.strategy_base import StrategyConfig
    
    # Khởi tạo strategies
    macd_strategy = VNMultiTimeframeMACDStrategy()
    ma_strategy = VNMultiTimeframeMAStrategy()
    
    # Test với symbol VN đầu tiên
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, ticker FROM symbols WHERE exchange = 'VN' LIMIT 1")
        symbol = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not symbol:
            print("❌ No VN symbols found")
            return
        
        symbol_id, symbol_ticker = symbol
        print(f"🎯 Testing with: {symbol_ticker} (ID: {symbol_id})")
        
        # Test MACD strategy
        print(f"\n📊 Testing MACD Strategy:")
        for tf in ["5m", "15m", "1h"]:
            result = macd_strategy.evaluate(symbol_id, tf, StrategyConfig())
            print(f"   {tf}: {result.direction.value} (Strength: {result.strength:.3f}, Confidence: {result.confidence:.3f})")
        
        # Test MA strategy
        print(f"\n📈 Testing MA Strategy:")
        for tf in ["5m", "15m", "1h"]:
            result = ma_strategy.evaluate(symbol_id, tf, StrategyConfig())
            print(f"   {tf}: {result.direction.value} (Strength: {result.strength:.3f}, Confidence: {result.confidence:.3f})")
        
    except Exception as e:
        print(f"❌ Error testing individual strategies: {e}")

if __name__ == "__main__":
    print("🚀 VN Multi-Timeframe Strategy Test")
    print("=" * 70)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test individual strategies first
    test_individual_strategies()
    
    # Test multi-timeframe engine
    test_vn_multi_timeframe_strategy()
    
    print(f"\n✅ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
