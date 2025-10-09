#!/usr/bin/env python3
"""
Signal Validation System - Kiểm chứng tính chính xác của tín hiệu
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import text
import json

# Add project root to path
sys.path.append('/code')

from app.db import init_db
from app.services.sma_signal_engine import sma_signal_engine

# Initialize DB
init_db(os.getenv("DATABASE_URL"))
from app.db import SessionLocal

class SignalValidator:
    """Class để kiểm chứng tính chính xác của tín hiệu"""
    
    def __init__(self):
        self.validation_results = []
    
    def validate_sma_signals(self, symbol_id: int, ticker: str, days_back: int = 7):
        """Kiểm chứng SMA signals với dữ liệu thực tế"""
        
        print(f"🔍 Validating SMA signals for {ticker} (last {days_back} days)")
        
        with SessionLocal() as s:
            # Lấy dữ liệu candles và SMA indicators
            candles_query = text("""
                SELECT ts, open, high, low, close, volume
                FROM candles_1m
                WHERE symbol_id = :symbol_id
                AND ts >= DATE_SUB(NOW(), INTERVAL :days DAY)
                ORDER BY ts
            """)
            
            candles_data = s.execute(candles_query, {
                'symbol_id': symbol_id,
                'days': days_back
            }).fetchall()
            
            if not candles_data:
                print(f"❌ No candle data found for {ticker}")
                return
            
            # Lấy SMA signals
            signals_query = text("""
                SELECT timeframe, timestamp, signal_type, signal_direction, 
                       signal_strength, current_price, ma18, ma36, ma48, ma144, avg_ma
                FROM sma_signals
                WHERE symbol_id = :symbol_id
                AND timestamp >= DATE_SUB(NOW(), INTERVAL :days DAY)
                ORDER BY timestamp
            """)
            
            signals_data = s.execute(signals_query, {
                'symbol_id': symbol_id,
                'days': days_back
            }).fetchall()
            
            if not signals_data:
                print(f"❌ No SMA signals found for {ticker}")
                return
            
            # Convert to DataFrames
            candles_df = pd.DataFrame(candles_data, columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
            signals_df = pd.DataFrame(signals_data, columns=[
                'timeframe', 'timestamp', 'signal_type', 'signal_direction',
                'signal_strength', 'current_price', 'ma18', 'ma36', 'ma48', 'ma144', 'avg_ma'
            ])
            
            # Validate each signal
            for _, signal in signals_df.iterrows():
                self._validate_single_signal(ticker, signal, candles_df)
    
    def _validate_single_signal(self, ticker: str, signal: pd.Series, candles_df: pd.DataFrame):
        """Kiểm chứng một tín hiệu cụ thể"""
        
        signal_time = signal['timestamp']
        timeframe = signal['timeframe']
        signal_type = signal['signal_type']
        signal_direction = signal['signal_direction']
        
        # Lấy dữ liệu candles tại thời điểm tín hiệu
        signal_candles = candles_df[candles_df['ts'] <= signal_time].tail(200)  # 200 candles gần nhất
        
        if len(signal_candles) < 50:
            return
        
        # Resample theo timeframe
        tf_candles = self._resample_candles(signal_candles, timeframe)
        
        if len(tf_candles) < 20:
            return
        
        # Tính toán SMA indicators
        sma_indicators = self._calculate_sma_indicators(tf_candles)
        
        # Tạo MA structure
        latest_candle = tf_candles.iloc[-1]
        ma_structure = {
            'cp': float(latest_candle['close']),
            'm1': float(sma_indicators['m1'].iloc[-1]),
            'm2': float(sma_indicators['m2'].iloc[-1]),
            'm3': float(sma_indicators['m3'].iloc[-1]),
            'ma144': float(sma_indicators['ma144'].iloc[-1]),
            'avg_m1_m2_m3': float(sma_indicators['avg_m1_m2_m3'].iloc[-1])
        }
        
        # Kiểm tra logic tín hiệu
        expected_signal = sma_signal_engine.evaluate_single_timeframe(ma_structure)
        
        # So sánh với tín hiệu thực tế
        is_correct = (expected_signal.value == signal_type)
        
        # Tính performance sau tín hiệu
        performance = self._calculate_signal_performance(
            signal_candles, signal_time, signal_direction, timeframe
        )
        
        validation_result = {
            'ticker': ticker,
            'timestamp': signal_time,
            'timeframe': timeframe,
            'signal_type': signal_type,
            'signal_direction': signal_direction,
            'expected_signal': expected_signal.value,
            'is_correct': is_correct,
            'ma_structure': ma_structure,
            'performance_1h': performance.get('1h', 0),
            'performance_4h': performance.get('4h', 0),
            'performance_1d': performance.get('1d', 0)
        }
        
        self.validation_results.append(validation_result)
        
        # Log kết quả
        status = "✅" if is_correct else "❌"
        print(f"  {status} {signal_time} {timeframe}: {signal_type} (expected: {expected_signal.value})")
        if not is_correct:
            print(f"    MA Structure: CP={ma_structure['cp']:.2f}, M1={ma_structure['m1']:.2f}, M2={ma_structure['m2']:.2f}, M3={ma_structure['m3']:.2f}, MA144={ma_structure['ma144']:.2f}")
    
    def _resample_candles(self, candles_df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """Resample candles theo timeframe"""
        
        candles_df['ts'] = pd.to_datetime(candles_df['ts'])
        candles_df.set_index('ts', inplace=True)
        
        # Resample theo timeframe
        if timeframe == '1m':
            return candles_df
        elif timeframe == '2m':
            return candles_df.resample('2T').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        elif timeframe == '5m':
            return candles_df.resample('5T').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        elif timeframe == '15m':
            return candles_df.resample('15T').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        elif timeframe == '30m':
            return candles_df.resample('30T').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        elif timeframe == '1h':
            return candles_df.resample('1H').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        elif timeframe == '4h':
            return candles_df.resample('4H').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        
        return candles_df
    
    def _calculate_sma_indicators(self, candles_df: pd.DataFrame) -> dict:
        """Tính toán SMA indicators"""
        
        close_prices = candles_df['close']
        
        # SMA periods
        m1 = close_prices.rolling(window=18, min_periods=1).mean()  # MA18
        m2 = close_prices.rolling(window=36, min_periods=1).mean()  # MA36
        m3 = close_prices.rolling(window=48, min_periods=1).mean()  # MA48
        ma144 = close_prices.rolling(window=144, min_periods=1).mean()  # MA144
        
        # Average of M1, M2, M3
        avg_m1_m2_m3 = (m1 + m2 + m3) / 3
        
        return {
            'm1': m1,
            'm2': m2,
            'm3': m3,
            'ma144': ma144,
            'avg_m1_m2_m3': avg_m1_m2_m3
        }
    
    def _calculate_signal_performance(self, candles_df: pd.DataFrame, signal_time: datetime, 
                                    signal_direction: str, timeframe: str) -> dict:
        """Tính performance sau tín hiệu"""
        
        signal_time = pd.to_datetime(signal_time)
        candles_df['ts'] = pd.to_datetime(candles_df['ts'])
        
        # Lấy giá tại thời điểm tín hiệu
        signal_price = candles_df[candles_df['ts'] <= signal_time]['close'].iloc[-1]
        
        performance = {}
        
        # Performance sau 1 giờ
        future_1h = signal_time + timedelta(hours=1)
        future_candles_1h = candles_df[candles_df['ts'] >= future_1h]
        if len(future_candles_1h) > 0:
            future_price_1h = future_candles_1h['close'].iloc[0]
            if signal_direction == 'BUY':
                performance['1h'] = ((future_price_1h - signal_price) / signal_price) * 100
            else:  # SELL
                performance['1h'] = ((signal_price - future_price_1h) / signal_price) * 100
        
        # Performance sau 4 giờ
        future_4h = signal_time + timedelta(hours=4)
        future_candles_4h = candles_df[candles_df['ts'] >= future_4h]
        if len(future_candles_4h) > 0:
            future_price_4h = future_candles_4h['close'].iloc[0]
            if signal_direction == 'BUY':
                performance['4h'] = ((future_price_4h - signal_price) / signal_price) * 100
            else:  # SELL
                performance['4h'] = ((signal_price - future_price_4h) / signal_price) * 100
        
        # Performance sau 1 ngày
        future_1d = signal_time + timedelta(days=1)
        future_candles_1d = candles_df[candles_df['ts'] >= future_1d]
        if len(future_candles_1d) > 0:
            future_price_1d = future_candles_1d['close'].iloc[0]
            if signal_direction == 'BUY':
                performance['1d'] = ((future_price_1d - signal_price) / signal_price) * 100
            else:  # SELL
                performance['1d'] = ((signal_price - future_price_1d) / signal_price) * 100
        
        return performance
    
    def generate_validation_report(self):
        """Tạo báo cáo kiểm chứng"""
        
        if not self.validation_results:
            print("❌ No validation results to report")
            return
        
        print(f"\n📊 SIGNAL VALIDATION REPORT")
        print("=" * 60)
        
        # Tính toán thống kê
        total_signals = len(self.validation_results)
        correct_signals = sum(1 for r in self.validation_results if r['is_correct'])
        accuracy = (correct_signals / total_signals) * 100 if total_signals > 0 else 0
        
        print(f"📈 Total Signals: {total_signals}")
        print(f"✅ Correct Signals: {correct_signals}")
        print(f"❌ Incorrect Signals: {total_signals - correct_signals}")
        print(f"🎯 Accuracy: {accuracy:.1f}%")
        
        # Performance analysis
        buy_signals = [r for r in self.validation_results if r['signal_direction'] == 'BUY']
        sell_signals = [r for r in self.validation_results if r['signal_direction'] == 'SELL']
        
        if buy_signals:
            avg_buy_performance_1h = np.mean([r['performance_1h'] for r in buy_signals if r['performance_1h'] != 0])
            avg_buy_performance_4h = np.mean([r['performance_4h'] for r in buy_signals if r['performance_4h'] != 0])
            avg_buy_performance_1d = np.mean([r['performance_1d'] for r in buy_signals if r['performance_1d'] != 0])
            
            print(f"\n📈 BUY Signals Performance:")
            print(f"   1h: {avg_buy_performance_1h:.2f}%")
            print(f"   4h: {avg_buy_performance_4h:.2f}%")
            print(f"   1d: {avg_buy_performance_1d:.2f}%")
        
        if sell_signals:
            avg_sell_performance_1h = np.mean([r['performance_1h'] for r in sell_signals if r['performance_1h'] != 0])
            avg_sell_performance_4h = np.mean([r['performance_4h'] for r in sell_signals if r['performance_4h'] != 0])
            avg_sell_performance_1d = np.mean([r['performance_1d'] for r in sell_signals if r['performance_1d'] != 0])
            
            print(f"\n📉 SELL Signals Performance:")
            print(f"   1h: {avg_sell_performance_1h:.2f}%")
            print(f"   4h: {avg_sell_performance_4h:.2f}%")
            print(f"   1d: {avg_sell_performance_1d:.2f}%")
        
        # Lưu báo cáo chi tiết
        report_file = f"signal_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.validation_results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed report saved to: {report_file}")

def main():
    """Main function"""
    
    print("🔍 SIGNAL VALIDATION SYSTEM")
    print("=" * 50)
    
    validator = SignalValidator()
    
    # Lấy danh sách symbols để validate
    with SessionLocal() as s:
        symbols_query = text("""
            SELECT id, ticker, exchange
            FROM symbols
            WHERE active = 1
            ORDER BY ticker
            LIMIT 5
        """)
        
        symbols = s.execute(symbols_query).fetchall()
    
    # Validate từng symbol
    for symbol_id, ticker, exchange in symbols:
        print(f"\n🔍 Validating {ticker} ({exchange})...")
        validator.validate_sma_signals(symbol_id, ticker, days_back=7)
    
    # Tạo báo cáo
    validator.generate_validation_report()

if __name__ == "__main__":
    main()
