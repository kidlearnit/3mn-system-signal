#!/usr/bin/env python3
"""
Market Comparison Tool - So sánh tín hiệu với dữ liệu thị trường thực tế
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import text
import yfinance as yf
import requests

# Add project root to path
sys.path.append('/code')

from app.db import SessionLocal, init_db

# Initialize DB
if SessionLocal is None:
    init_db(os.getenv("DATABASE_URL"))

class MarketComparison:
    """Class để so sánh tín hiệu với dữ liệu thị trường thực tế"""
    
    def __init__(self):
        self.comparison_results = []
    
    def compare_with_yahoo_finance(self, symbol_id: int, ticker: str, days_back: int = 7):
        """So sánh với dữ liệu Yahoo Finance"""
        
        print(f"🔍 Comparing {ticker} with Yahoo Finance data (last {days_back} days)")
        
        try:
            # Lấy dữ liệu từ Yahoo Finance
            yf_ticker = yf.Ticker(ticker)
            yf_data = yf_ticker.history(period=f"{days_back}d", interval="1m")
            
            if yf_data.empty:
                print(f"❌ No Yahoo Finance data for {ticker}")
                return
            
            # Lấy dữ liệu từ database
            with SessionLocal() as s:
                db_data_query = text("""
                    SELECT ts, open, high, low, close, volume
                    FROM candles_1m
                    WHERE symbol_id = :symbol_id
                    AND ts >= DATE_SUB(NOW(), INTERVAL :days DAY)
                    ORDER BY ts
                """)
                
                db_data = s.execute(db_data_query, {
                    'symbol_id': symbol_id,
                    'days': days_back
                }).fetchall()
                
                if not db_data:
                    print(f"❌ No database data for {ticker}")
                    return
                
                db_df = pd.DataFrame(db_data, columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
                db_df['ts'] = pd.to_datetime(db_df['ts'])
                db_df.set_index('ts', inplace=True)
            
            # So sánh dữ liệu
            self._compare_price_data(ticker, yf_data, db_df)
            
        except Exception as e:
            print(f"❌ Error comparing with Yahoo Finance: {e}")
    
    def _compare_price_data(self, ticker: str, yf_data: pd.DataFrame, db_data: pd.DataFrame):
        """So sánh dữ liệu giá"""
        
        print(f"\n📊 PRICE DATA COMPARISON for {ticker}")
        print("=" * 50)
        
        # Lấy dữ liệu chung (cùng thời gian)
        common_times = yf_data.index.intersection(db_data.index)
        
        if len(common_times) == 0:
            print("❌ No common time periods found")
            return
        
        yf_common = yf_data.loc[common_times]
        db_common = db_data.loc[common_times]
        
        print(f"📈 Common time periods: {len(common_times)}")
        
        # So sánh giá close
        close_diff = abs(yf_common['Close'] - db_common['close'])
        close_diff_pct = (close_diff / yf_common['Close']) * 100
        
        print(f"\n💰 CLOSE PRICE COMPARISON:")
        print(f"   Average difference: ${close_diff.mean():.4f}")
        print(f"   Max difference: ${close_diff.max():.4f}")
        print(f"   Average difference %: {close_diff_pct.mean():.2f}%")
        print(f"   Max difference %: {close_diff_pct.max():.2f}%")
        
        # So sánh volume
        volume_diff = abs(yf_common['Volume'] - db_common['volume'])
        volume_diff_pct = (volume_diff / yf_common['Volume']) * 100
        
        print(f"\n📊 VOLUME COMPARISON:")
        print(f"   Average difference: {volume_diff.mean():.0f}")
        print(f"   Max difference: {volume_diff.max():.0f}")
        print(f"   Average difference %: {volume_diff_pct.mean():.2f}%")
        print(f"   Max difference %: {volume_diff_pct.max():.2f}%")
        
        # Đánh giá độ chính xác
        accuracy_score = self._calculate_accuracy_score(close_diff_pct, volume_diff_pct)
        print(f"\n🎯 ACCURACY SCORE: {accuracy_score:.1f}/100")
        
        if accuracy_score >= 95:
            print("✅ Excellent data accuracy!")
        elif accuracy_score >= 90:
            print("✅ Good data accuracy")
        elif accuracy_score >= 80:
            print("⚠️  Fair data accuracy")
        else:
            print("❌ Poor data accuracy - needs investigation")
    
    def _calculate_accuracy_score(self, close_diff_pct: pd.Series, volume_diff_pct: pd.Series) -> float:
        """Tính điểm độ chính xác"""
        
        # Điểm cho close price (70% trọng số)
        close_score = max(0, 100 - close_diff_pct.mean() * 10)
        
        # Điểm cho volume (30% trọng số)
        volume_score = max(0, 100 - volume_diff_pct.mean() * 2)
        
        # Tổng điểm
        total_score = (close_score * 0.7) + (volume_score * 0.3)
        
        return min(100, total_score)
    
    def compare_signals_with_market_trend(self, symbol_id: int, ticker: str, days_back: int = 7):
        """So sánh tín hiệu với xu hướng thị trường thực tế"""
        
        print(f"🔍 Comparing signals with market trend for {ticker}")
        
        try:
            # Lấy dữ liệu Yahoo Finance
            yf_ticker = yf.Ticker(ticker)
            yf_data = yf_ticker.history(period=f"{days_back}d", interval="1h")
            
            if yf_data.empty:
                print(f"❌ No Yahoo Finance data for {ticker}")
                return
            
            # Lấy tín hiệu từ database
            with SessionLocal() as s:
                signals_query = text("""
                    SELECT timeframe, timestamp, signal_type, signal_direction, signal_strength
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
                    print(f"❌ No signals found for {ticker}")
                    return
                
                signals_df = pd.DataFrame(signals_data, columns=[
                    'timeframe', 'timestamp', 'signal_type', 'signal_direction', 'signal_strength'
                ])
            
            # Phân tích xu hướng thị trường
            market_trends = self._analyze_market_trends(yf_data)
            
            # So sánh tín hiệu với xu hướng
            self._compare_signals_with_trends(ticker, signals_df, market_trends)
            
        except Exception as e:
            print(f"❌ Error comparing signals with market trend: {e}")
    
    def _analyze_market_trends(self, yf_data: pd.DataFrame) -> dict:
        """Phân tích xu hướng thị trường"""
        
        trends = {}
        
        # Tính SMA
        yf_data['SMA_20'] = yf_data['Close'].rolling(window=20).mean()
        yf_data['SMA_50'] = yf_data['Close'].rolling(window=50).mean()
        
        # Xác định xu hướng
        for i in range(1, len(yf_data)):
            current_price = yf_data['Close'].iloc[i]
            prev_price = yf_data['Close'].iloc[i-1]
            sma_20 = yf_data['SMA_20'].iloc[i]
            sma_50 = yf_data['SMA_50'].iloc[i]
            
            timestamp = yf_data.index[i]
            
            # Xác định xu hướng
            if current_price > sma_20 > sma_50:
                trend = "BULLISH"
            elif current_price < sma_20 < sma_50:
                trend = "BEARISH"
            else:
                trend = "NEUTRAL"
            
            trends[timestamp] = {
                'trend': trend,
                'price': current_price,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'price_change': ((current_price - prev_price) / prev_price) * 100
            }
        
        return trends
    
    def _compare_signals_with_trends(self, ticker: str, signals_df: pd.DataFrame, market_trends: dict):
        """So sánh tín hiệu với xu hướng thị trường"""
        
        print(f"\n📊 SIGNAL vs MARKET TREND COMPARISON for {ticker}")
        print("=" * 60)
        
        correct_predictions = 0
        total_predictions = 0
        
        for _, signal in signals_df.iterrows():
            signal_time = pd.to_datetime(signal['timestamp'])
            signal_direction = signal['signal_direction']
            
            # Tìm xu hướng thị trường gần nhất
            market_trend = self._find_closest_market_trend(signal_time, market_trends)
            
            if market_trend:
                # So sánh tín hiệu với xu hướng
                is_correct = self._is_signal_correct(signal_direction, market_trend)
                
                if is_correct is not None:
                    correct_predictions += is_correct
                    total_predictions += 1
                    
                    status = "✅" if is_correct else "❌"
                    print(f"   {status} {signal_time} {signal['timeframe']}: {signal_direction} vs {market_trend['trend']} (Price: ${market_trend['price']:.2f})")
        
        if total_predictions > 0:
            accuracy = (correct_predictions / total_predictions) * 100
            print(f"\n🎯 SIGNAL ACCURACY: {accuracy:.1f}% ({correct_predictions}/{total_predictions})")
            
            if accuracy >= 70:
                print("✅ Good signal accuracy!")
            elif accuracy >= 60:
                print("⚠️  Fair signal accuracy")
            else:
                print("❌ Poor signal accuracy - needs improvement")
        else:
            print("❌ No comparable signals found")
    
    def _find_closest_market_trend(self, signal_time: pd.Timestamp, market_trends: dict) -> dict:
        """Tìm xu hướng thị trường gần nhất với thời điểm tín hiệu"""
        
        closest_time = None
        min_diff = float('inf')
        
        for trend_time in market_trends.keys():
            diff = abs((signal_time - trend_time).total_seconds())
            if diff < min_diff and diff <= 3600:  # Trong vòng 1 giờ
                min_diff = diff
                closest_time = trend_time
        
        return market_trends.get(closest_time) if closest_time else None
    
    def _is_signal_correct(self, signal_direction: str, market_trend: dict) -> bool:
        """Kiểm tra tín hiệu có đúng với xu hướng thị trường không"""
        
        if signal_direction == 'BUY' and market_trend['trend'] == 'BULLISH':
            return True
        elif signal_direction == 'SELL' and market_trend['trend'] == 'BEARISH':
            return True
        elif signal_direction == 'HOLD' and market_trend['trend'] == 'NEUTRAL':
            return True
        else:
            return False

def main():
    """Main function"""
    
    print("🔍 MARKET COMPARISON TOOL")
    print("=" * 50)
    
    comparator = MarketComparison()
    
    # Lấy symbol để so sánh
    with SessionLocal() as s:
        symbols_query = text("""
            SELECT id, ticker, exchange
            FROM symbols
            WHERE active = 1
            AND exchange IN ('NASDAQ', 'NYSE')
            ORDER BY ticker
            LIMIT 3
        """)
        
        symbols = s.execute(symbols_query).fetchall()
    
    if not symbols:
        print("❌ No symbols found")
        return
    
    # So sánh từng symbol
    for symbol_id, ticker, exchange in symbols:
        print(f"\n🎯 Comparing {ticker} ({exchange})")
        
        # So sánh dữ liệu giá
        comparator.compare_with_yahoo_finance(symbol_id, ticker, days_back=7)
        
        # So sánh tín hiệu với xu hướng
        comparator.compare_signals_with_market_trend(symbol_id, ticker, days_back=7)
        
        print("\n" + "="*60)

if __name__ == "__main__":
    main()
