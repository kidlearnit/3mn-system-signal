#!/usr/bin/env python3
"""
Simple Signal Checker - Kiểm chứng tín hiệu đơn giản
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text

# Add project root to path
sys.path.append('/code')

from app.db import init_db
init_db(os.getenv("DATABASE_URL"))
from app.db import SessionLocal

def check_recent_signals():
    """Kiểm tra tín hiệu gần đây"""
    
    print("🔍 KIỂM CHỨNG TÍN HIỆU GẦN ĐÂY")
    print("=" * 50)
    
    with SessionLocal() as s:
        # Lấy tín hiệu gần đây
        signals_query = text("""
            SELECT s.ticker, sma.timeframe, sma.timestamp, sma.signal_type, 
                   sma.signal_direction, sma.signal_strength, sma.current_price,
                   sma.ma18, sma.ma36, sma.ma48, sma.ma144, sma.avg_ma
            FROM sma_signals sma
            JOIN symbols s ON sma.symbol_id = s.id
            WHERE sma.timestamp >= DATE_SUB(NOW(), INTERVAL 2 HOUR)
            ORDER BY sma.timestamp DESC
            LIMIT 20
        """)
        
        signals_data = s.execute(signals_query).fetchall()
        
        if not signals_data:
            print("❌ Không có tín hiệu gần đây")
            return
        
        print(f"📊 Tìm thấy {len(signals_data)} tín hiệu gần đây:")
        print()
        
        for signal in signals_data:
            ticker, timeframe, timestamp, signal_type, signal_direction, signal_strength, current_price, ma18, ma36, ma48, ma144, avg_ma = signal
            
            print(f"📈 {ticker} {timeframe} - {timestamp}")
            print(f"   Signal: {signal_type} ({signal_direction}) - Strength: {signal_strength}")
            print(f"   Price: ${current_price:.2f}")
            print(f"   MA18: {ma18:.2f}, MA36: {ma36:.2f}, MA48: {ma48:.2f}, MA144: {ma144:.2f}")
            print(f"   AVG: {avg_ma:.2f}")
            
            # Kiểm tra logic cơ bản
            if signal_direction == 'BUY':
                if current_price > ma18 > ma36 > ma48:
                    print("   ✅ Logic BUY: Price > MA18 > MA36 > MA48")
                else:
                    print("   ❌ Logic BUY: Không thỏa mãn điều kiện")
            elif signal_direction == 'SELL':
                if current_price < ma18 < ma36 < ma48:
                    print("   ✅ Logic SELL: Price < MA18 < MA36 < MA48")
                else:
                    print("   ❌ Logic SELL: Không thỏa mãn điều kiện")
            else:
                print("   ⚪ HOLD signal")
            
            print()

def check_signal_accuracy():
    """Kiểm tra độ chính xác của tín hiệu"""
    
    print("🎯 KIỂM TRA ĐỘ CHÍNH XÁC TÍN HIỆU")
    print("=" * 50)
    
    with SessionLocal() as s:
        # Lấy tín hiệu trong 24h qua
        signals_query = text("""
            SELECT s.ticker, sma.timeframe, sma.timestamp, sma.signal_type, 
                   sma.signal_direction, sma.signal_strength, sma.current_price
            FROM sma_signals sma
            JOIN symbols s ON sma.symbol_id = s.id
            WHERE sma.timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            AND sma.signal_direction IN ('BUY', 'SELL')
            ORDER BY sma.timestamp DESC
        """)
        
        signals_data = s.execute(signals_query).fetchall()
        
        if not signals_data:
            print("❌ Không có tín hiệu BUY/SELL trong 24h qua")
            return
        
        print(f"📊 Tìm thấy {len(signals_data)} tín hiệu BUY/SELL trong 24h:")
        print()
        
        # Phân tích theo loại tín hiệu
        buy_signals = [s for s in signals_data if s[4] == 'BUY']
        sell_signals = [s for s in signals_data if s[4] == 'SELL']
        
        print(f"📈 BUY signals: {len(buy_signals)}")
        print(f"📉 SELL signals: {len(sell_signals)}")
        print()
        
        # Phân tích theo strength
        strong_signals = [s for s in signals_data if s[5] and s[5] > 0.5]
        medium_signals = [s for s in signals_data if s[5] and 0.2 <= s[5] <= 0.5]
        weak_signals = [s for s in signals_data if s[5] and s[5] < 0.2]
        
        print(f"💪 Strong signals (>0.5): {len(strong_signals)}")
        print(f"⚖️  Medium signals (0.2-0.5): {len(medium_signals)}")
        print(f"💤 Weak signals (<0.2): {len(weak_signals)}")
        print()
        
        # Phân tích theo timeframe
        timeframe_counts = {}
        for signal in signals_data:
            tf = signal[1]
            timeframe_counts[tf] = timeframe_counts.get(tf, 0) + 1
        
        print("⏰ Signals theo timeframe:")
        for tf, count in sorted(timeframe_counts.items()):
            print(f"   {tf}: {count} signals")
        print()
        
        # Phân tích theo symbol
        symbol_counts = {}
        for signal in signals_data:
            ticker = signal[0]
            symbol_counts[ticker] = symbol_counts.get(ticker, 0) + 1
        
        print("📊 Signals theo symbol:")
        for ticker, count in sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {ticker}: {count} signals")

def check_market_conditions():
    """Kiểm tra điều kiện thị trường"""
    
    print("🌍 KIỂM TRA ĐIỀU KIỆN THỊ TRƯỜNG")
    print("=" * 50)
    
    with SessionLocal() as s:
        # Lấy dữ liệu giá mới nhất
        price_query = text("""
            SELECT s.ticker, s.exchange, c.close, c.ts
            FROM candles_1m c
            JOIN symbols s ON c.symbol_id = s.id
            WHERE c.ts >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
            AND s.active = 1
            ORDER BY c.ts DESC
            LIMIT 10
        """)
        
        price_data = s.execute(price_query).fetchall()
        
        if not price_data:
            print("❌ Không có dữ liệu giá gần đây")
            return
        
        print("📊 Giá mới nhất:")
        for ticker, exchange, price, timestamp in price_data:
            print(f"   {ticker} ({exchange}): ${price:.2f} - {timestamp}")
        print()
        
        # Kiểm tra thị trường mở
        from utils.market_time import is_market_open
        
        us_market_open = is_market_open("NASDAQ")
        vn_market_open = is_market_open("HOSE")
        
        print("🕐 Trạng thái thị trường:")
        print(f"   US Market (NASDAQ): {'🟢 Mở' if us_market_open else '🔴 Đóng'}")
        print(f"   VN Market (HOSE): {'🟢 Mở' if vn_market_open else '🔴 Đóng'}")

def main():
    """Main function"""
    
    print("🔍 SIMPLE SIGNAL CHECKER")
    print("=" * 50)
    print()
    
    # Kiểm tra tín hiệu gần đây
    check_recent_signals()
    print()
    
    # Kiểm tra độ chính xác
    check_signal_accuracy()
    print()
    
    # Kiểm tra điều kiện thị trường
    check_market_conditions()
    print()
    
    print("✅ Kiểm tra hoàn tất!")

if __name__ == "__main__":
    main()
