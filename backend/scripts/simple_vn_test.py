#!/usr/bin/env python3
"""
Simple test cho VN Multi-Timeframe Strategy
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
import os
from dotenv import load_dotenv
import json
from datetime import datetime

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

def test_vn_symbols():
    """Test VN symbols và data availability"""
    print("🚀 Testing VN Symbols and Data")
    print("=" * 50)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Check VN symbols
        print("\n📊 Checking VN symbols...")
        cursor.execute("""
            SELECT id, ticker, exchange, name
            FROM symbols 
            WHERE exchange = 'VN' 
            ORDER BY ticker 
            LIMIT 10
        """)
        
        vn_symbols = cursor.fetchall()
        
        if not vn_symbols:
            print("❌ No VN symbols found in database")
            return
        
        print(f"✅ Found {len(vn_symbols)} VN symbols:")
        for symbol in vn_symbols:
            print(f"   - {symbol[1]} ({symbol[2]}) - ID: {symbol[0]} - {symbol[3]}")
        
        # 2. Check data availability for first symbol
        test_symbol = vn_symbols[0]
        symbol_id = test_symbol[0]
        symbol_ticker = test_symbol[1]
        
        print(f"\n🔍 Checking data for {symbol_ticker} (ID: {symbol_id})...")
        
        # Check candles
        cursor.execute("""
            SELECT timeframe, COUNT(*) as count, MAX(timestamp) as latest
            FROM candles 
            WHERE symbol_id = %s 
            GROUP BY timeframe
            ORDER BY timeframe
        """, (symbol_id,))
        
        candle_data = cursor.fetchall()
        
        if candle_data:
            print("   📈 Candle data:")
            for tf, count, latest in candle_data:
                print(f"      {tf}: {count} candles, latest: {latest}")
        else:
            print("   ❌ No candle data found")
        
        # Check MACD indicators
        cursor.execute("""
            SELECT timeframe, COUNT(*) as count, MAX(timestamp) as latest
            FROM indicators_macd 
            WHERE symbol_id = %s 
            GROUP BY timeframe
            ORDER BY timeframe
        """, (symbol_id,))
        
        macd_data = cursor.fetchall()
        
        if macd_data:
            print("   📊 MACD indicators:")
            for tf, count, latest in macd_data:
                print(f"      {tf}: {count} records, latest: {latest}")
        else:
            print("   ❌ No MACD data found")
        
        # Check SMA indicators
        cursor.execute("""
            SELECT timeframe, COUNT(*) as count, MAX(timestamp) as latest
            FROM indicators_sma 
            WHERE symbol_id = %s 
            GROUP BY timeframe
            ORDER BY timeframe
        """, (symbol_id,))
        
        sma_data = cursor.fetchall()
        
        if sma_data:
            print("   📈 SMA indicators:")
            for tf, count, latest in sma_data:
                print(f"      {tf}: {count} records, latest: {latest}")
        else:
            print("   ❌ No SMA data found")
        
        # 3. Test simple signal calculation
        print(f"\n🧮 Testing simple signal calculation for {symbol_ticker}...")
        
        # Get latest MACD data for 5m timeframe
        cursor.execute("""
            SELECT timestamp, macd, macd_signal, macd_histogram
            FROM indicators_macd 
            WHERE symbol_id = %s AND timeframe = '5m'
            ORDER BY timestamp DESC 
            LIMIT 5
        """, (symbol_id,))
        
        macd_records = cursor.fetchall()
        
        if macd_records:
            print("   📊 Latest MACD data (5m):")
            for i, (timestamp, macd, signal, histogram) in enumerate(macd_records):
                print(f"      {i+1}. {timestamp}: MACD={macd:.4f}, Signal={signal:.4f}, Hist={histogram:.4f}")
            
            # Simple signal logic
            latest = macd_records[0]
            prev = macd_records[1] if len(macd_records) > 1 else None
            
            if prev:
                current_macd, current_signal, current_hist = latest[1], latest[2], latest[3]
                prev_macd, prev_signal, prev_hist = prev[1], prev[2], prev[3]
                
                print(f"\n   🎯 Signal Analysis:")
                print(f"      Current MACD: {current_macd:.4f}")
                print(f"      Current Signal: {current_signal:.4f}")
                print(f"      Current Histogram: {current_hist:.4f}")
                
                # MACD crossover
                if current_macd > current_signal and prev_macd <= prev_signal:
                    print(f"      🟢 SIGNAL: BUY (MACD Bullish Crossover)")
                elif current_macd < current_signal and prev_macd >= prev_signal:
                    print(f"      🔴 SIGNAL: SELL (MACD Bearish Crossover)")
                else:
                    print(f"      ⚪ SIGNAL: NEUTRAL (No crossover)")
                
                # Histogram momentum
                if current_hist > prev_hist and current_hist > 0:
                    print(f"      📈 Momentum: Bullish (Histogram increasing)")
                elif current_hist < prev_hist and current_hist < 0:
                    print(f"      📉 Momentum: Bearish (Histogram decreasing)")
                else:
                    print(f"      ➡️  Momentum: Neutral")
        
        # Get latest SMA data for 5m timeframe
        cursor.execute("""
            SELECT timestamp, sma_18, sma_36, sma_48, sma_144, close
            FROM indicators_sma 
            WHERE symbol_id = %s AND timeframe = '5m'
            ORDER BY timestamp DESC 
            LIMIT 5
        """, (symbol_id,))
        
        sma_records = cursor.fetchall()
        
        if sma_records:
            print(f"\n   📈 Latest SMA data (5m):")
            for i, (timestamp, sma_18, sma_36, sma_48, sma_144, close) in enumerate(sma_records):
                print(f"      {i+1}. {timestamp}: Close={close:.2f}, SMA18={sma_18:.2f}, SMA36={sma_36:.2f}, SMA48={sma_48:.2f}, SMA144={sma_144:.2f}")
            
            # Simple MA signal logic
            latest = sma_records[0]
            prev = sma_records[1] if len(sma_records) > 1 else None
            
            if prev:
                current_close = latest[5]
                current_sma_18, current_sma_36, current_sma_48, current_sma_144 = latest[1], latest[2], latest[3], latest[4]
                prev_close = prev[5]
                prev_sma_18, prev_sma_36, prev_sma_48, prev_sma_144 = prev[1], prev[2], prev[3], prev[4]
                
                print(f"\n   🎯 MA Signal Analysis:")
                
                # Triple confirmation
                bullish_signals = 0
                bearish_signals = 0
                
                # 1. Price vs MA144
                if current_close > current_sma_144:
                    bullish_signals += 1
                    print(f"      ✅ Price > SMA144 (Bullish)")
                else:
                    bearish_signals += 1
                    print(f"      ❌ Price < SMA144 (Bearish)")
                
                # 2. MA18 vs MA36
                if current_sma_18 > current_sma_36:
                    bullish_signals += 1
                    print(f"      ✅ SMA18 > SMA36 (Bullish)")
                else:
                    bearish_signals += 1
                    print(f"      ❌ SMA18 < SMA36 (Bearish)")
                
                # 3. MA36 vs MA48
                if current_sma_36 > current_sma_48:
                    bullish_signals += 1
                    print(f"      ✅ SMA36 > SMA48 (Bullish)")
                else:
                    bearish_signals += 1
                    print(f"      ❌ SMA36 < SMA48 (Bearish)")
                
                # 4. Price momentum
                if current_close > prev_close:
                    bullish_signals += 1
                    print(f"      ✅ Price rising (Bullish)")
                else:
                    bearish_signals += 1
                    print(f"      ❌ Price falling (Bearish)")
                
                # 5. MA18 momentum
                if current_sma_18 > prev_sma_18:
                    bullish_signals += 1
                    print(f"      ✅ SMA18 rising (Bullish)")
                else:
                    bearish_signals += 1
                    print(f"      ❌ SMA18 falling (Bearish)")
                
                print(f"\n      📊 Signal Summary:")
                print(f"         Bullish signals: {bullish_signals}/5")
                print(f"         Bearish signals: {bearish_signals}/5")
                
                if bullish_signals >= 4:
                    print(f"         🟢 MA SIGNAL: STRONG BUY")
                elif bullish_signals >= 3:
                    print(f"         🟡 MA SIGNAL: WEAK BUY")
                elif bearish_signals >= 4:
                    print(f"         🔴 MA SIGNAL: STRONG SELL")
                elif bearish_signals >= 3:
                    print(f"         🟠 MA SIGNAL: WEAK SELL")
                else:
                    print(f"         ⚪ MA SIGNAL: NEUTRAL")
        
        cursor.close()
        conn.close()
        
        print(f"\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Simple VN Strategy Test")
    print("=" * 50)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_vn_symbols()
    
    print(f"\n✅ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
