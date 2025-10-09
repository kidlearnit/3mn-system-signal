#!/usr/bin/env python3
"""
Real-time Signal Checker - Kiểm chứng tín hiệu real-time
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import text
import time

# Add project root to path
sys.path.append('/code')

from app.db import SessionLocal, init_db
from app.services.sma_signal_engine import sma_signal_engine
from app.services.sma_indicators import sma_indicator_service
from app.services.candle_utils import load_candles_1m_df
from app.services.resample import resample_ohlcv

# Initialize DB
if SessionLocal is None:
    init_db(os.getenv("DATABASE_URL"))

class RealTimeSignalChecker:
    """Class để kiểm chứng tín hiệu real-time"""
    
    def __init__(self):
        self.check_results = []
    
    def check_latest_signals(self, symbol_id: int, ticker: str):
        """Kiểm chứng tín hiệu mới nhất"""
        
        print(f"🔍 Checking latest signals for {ticker}")
        
        with SessionLocal() as s:
            # Lấy tín hiệu mới nhất
            latest_signals_query = text("""
                SELECT timeframe, timestamp, signal_type, signal_direction, 
                       signal_strength, current_price, m1, m2, m3, ma144, avg_ma
                FROM sma_signals
                WHERE symbol_id = :symbol_id
                AND timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            
            signals_data = s.execute(latest_signals_query, {'symbol_id': symbol_id}).fetchall()
            
            if not signals_data:
                print(f"❌ No recent signals found for {ticker}")
                return
            
            # Lấy dữ liệu candles
            df_1m = load_candles_1m_df(symbol_id)
            if df_1m.empty:
                print(f"❌ No candle data found for {ticker}")
                return
            
            # Kiểm chứng từng tín hiệu
            for signal_data in signals_data:
                self._check_single_signal(ticker, signal_data, df_1m)
    
    def _check_single_signal(self, ticker: str, signal_data: tuple, df_1m: pd.DataFrame):
        """Kiểm chứng một tín hiệu cụ thể"""
        
        timeframe, timestamp, signal_type, signal_direction, signal_strength, current_price, m1, m2, m3, ma144, avg_ma = signal_data
        
        print(f"\n📊 Checking signal: {ticker} {timeframe} at {timestamp}")
        print(f"   Signal: {signal_type} ({signal_direction}) - Strength: {signal_strength}")
        print(f"   Price: {current_price}, M1: {m1}, M2: {m2}, M3: {m3}, MA144: {ma144}")
        
        # Resample data theo timeframe
        df_tf = resample_ohlcv(df_1m, timeframe)
        
        if df_tf.empty:
            print(f"❌ No {timeframe} data available")
            return
        
        # Tính toán SMA indicators
        sma_results = sma_indicator_service.calculate_all_smas(df_tf)
        
        if not sma_results:
            print(f"❌ Could not calculate SMA indicators")
            return
        
        # Lấy MA structure mới nhất
        latest_idx = df_tf.index[-1]
        ma_structure = {
            'cp': float(df_tf['close'].iloc[-1]),
            'm1': float(sma_results['m1'].iloc[-1]) if 'm1' in sma_results else 0.0,
            'm2': float(sma_results['m2'].iloc[-1]) if 'm2' in sma_results else 0.0,
            'm3': float(sma_results['m3'].iloc[-1]) if 'm3' in sma_results else 0.0,
            'ma144': float(sma_results['ma144'].iloc[-1]) if 'ma144' in sma_results else 0.0,
            'avg_m1_m2_m3': float(sma_results['avg_m1_m2_m3'].iloc[-1]) if 'avg_m1_m2_m3' in sma_results else 0.0
        }
        
        print(f"   Current MA Structure:")
        print(f"     CP: {ma_structure['cp']:.2f}")
        print(f"     M1: {ma_structure['m1']:.2f}")
        print(f"     M2: {ma_structure['m2']:.2f}")
        print(f"     M3: {ma_structure['m3']:.2f}")
        print(f"     MA144: {ma_structure['ma144']:.2f}")
        print(f"     AVG: {ma_structure['avg_m1_m2_m3']:.2f}")
        
        # Kiểm tra logic
        expected_signal = sma_signal_engine.evaluate_single_timeframe(ma_structure)
        
        print(f"   Expected Signal: {expected_signal.value}")
        
        # So sánh
        is_correct = (expected_signal.value == signal_type)
        status = "✅ CORRECT" if is_correct else "❌ INCORRECT"
        
        print(f"   Result: {status}")
        
        if not is_correct:
            print(f"   ⚠️  Signal mismatch detected!")
            print(f"   ⚠️  Stored: {signal_type}")
            print(f"   ⚠️  Expected: {expected_signal.value}")
            
            # Phân tích chi tiết
            self._analyze_signal_logic(ma_structure, signal_type, expected_signal.value)
        
        # Kiểm tra performance
        self._check_signal_performance(ticker, timestamp, signal_direction, df_1m)
    
    def _analyze_signal_logic(self, ma_structure: dict, stored_signal: str, expected_signal: str):
        """Phân tích logic tín hiệu chi tiết"""
        
        print(f"\n🔍 DETAILED LOGIC ANALYSIS:")
        
        cp = ma_structure['cp']
        m1 = ma_structure['m1']
        m2 = ma_structure['m2']
        m3 = ma_structure['m3']
        ma144 = ma_structure['ma144']
        avg_ma = ma_structure['avg_m1_m2_m3']
        
        # Kiểm tra Local Bullish Broken
        bullish_broken = cp > m1 > m2 > m3
        print(f"   Local Bullish Broken: {bullish_broken} (CP={cp:.2f} > M1={m1:.2f} > M2={m2:.2f} > M3={m3:.2f})")
        
        # Kiểm tra Local Bearish Broken
        bearish_broken = cp < m1 < m2 < m3
        print(f"   Local Bearish Broken: {bearish_broken} (CP={cp:.2f} < M1={m1:.2f} < M2={m2:.2f} < M3={m3:.2f})")
        
        # Kiểm tra Local Bullish
        local_bullish = bullish_broken and (avg_ma > ma144)
        print(f"   Local Bullish: {local_bullish} (Bullish Broken={bullish_broken} AND AVG={avg_ma:.2f} > MA144={ma144:.2f})")
        
        # Kiểm tra Local Bearish
        local_bearish = bearish_broken and (avg_ma < ma144)
        print(f"   Local Bearish: {local_bearish} (Bearish Broken={bearish_broken} AND AVG={avg_ma:.2f} < MA144={ma144:.2f})")
        
        # Kết luận
        if local_bullish:
            print(f"   ✅ Should be: local_bullish")
        elif local_bullish_broken:
            print(f"   ✅ Should be: local_bullish_broken")
        elif local_bearish:
            print(f"   ✅ Should be: local_bearish")
        elif bearish_broken:
            print(f"   ✅ Should be: local_bearish_broken")
        else:
            print(f"   ✅ Should be: neutral")
    
    def _check_signal_performance(self, ticker: str, signal_time: datetime, signal_direction: str, df_1m: pd.DataFrame):
        """Kiểm tra performance của tín hiệu"""
        
        signal_time = pd.to_datetime(signal_time)
        df_1m['ts'] = pd.to_datetime(df_1m['ts'])
        
        # Lấy giá tại thời điểm tín hiệu
        signal_price = df_1m[df_1m['ts'] <= signal_time]['close'].iloc[-1]
        
        # Lấy giá hiện tại
        current_price = df_1m['close'].iloc[-1]
        
        # Tính performance
        if signal_direction == 'BUY':
            performance = ((current_price - signal_price) / signal_price) * 100
        else:  # SELL
            performance = ((signal_price - current_price) / signal_price) * 100
        
        print(f"\n📈 SIGNAL PERFORMANCE:")
        print(f"   Signal Price: {signal_price:.2f}")
        print(f"   Current Price: {current_price:.2f}")
        print(f"   Performance: {performance:.2f}%")
        
        if performance > 0:
            print(f"   ✅ Signal is profitable!")
        else:
            print(f"   ❌ Signal is losing money")
    
    def monitor_signals(self, symbol_id: int, ticker: str, duration_minutes: int = 60):
        """Monitor tín hiệu trong thời gian thực"""
        
        print(f"🔍 Monitoring signals for {ticker} for {duration_minutes} minutes...")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        while datetime.now() < end_time:
            print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - Checking {ticker}...")
            
            self.check_latest_signals(symbol_id, ticker)
            
            # Đợi 5 phút
            time.sleep(300)  # 5 minutes
        
        print(f"\n✅ Monitoring completed for {ticker}")

def main():
    """Main function"""
    
    print("🔍 REAL-TIME SIGNAL CHECKER")
    print("=" * 50)
    
    checker = RealTimeSignalChecker()
    
    # Lấy symbol để check
    with SessionLocal() as s:
        symbols_query = text("""
            SELECT id, ticker, exchange
            FROM symbols
            WHERE active = 1
            AND ticker IN ('AAPL', 'MSFT', 'GOOGL')
            ORDER BY ticker
            LIMIT 1
        """)
        
        symbols = s.execute(symbols_query).fetchall()
    
    if not symbols:
        print("❌ No symbols found")
        return
    
    symbol_id, ticker, exchange = symbols[0]
    
    print(f"🎯 Checking signals for {ticker} ({exchange})")
    
    # Check latest signals
    checker.check_latest_signals(symbol_id, ticker)
    
    # Ask user if they want to monitor
    response = input("\n🔍 Do you want to monitor signals in real-time? (y/n): ")
    if response.lower() == 'y':
        duration = int(input("⏰ How many minutes to monitor? (default 60): ") or "60")
        checker.monitor_signals(symbol_id, ticker, duration)

if __name__ == "__main__":
    main()
