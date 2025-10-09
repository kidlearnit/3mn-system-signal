"""
Multi-Timeframe Chart Service - Gửi chart 7 khung thời gian với MACD
"""
import os
import tempfile
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from datetime import datetime, timezone, timedelta
import requests
from typing import Dict, List, Optional
import numpy as np

class MultiTimeframeChartService:
    def __init__(self):
        self.tg_token = os.getenv('TG_TOKEN')
        self.tg_chat_id = os.getenv('TG_CHAT_ID')
        
        # 7 khung thời gian theo cấu hình hệ thống
        self.timeframes = ['1m', '2m', '5m', '15m', '30m', '1h', '4h']
        self.tf_weights = {
            '1m': 2,    # Khung nhỏ - tìm điểm vào lệnh
            '2m': 3,    # Khung nhỏ - tìm điểm vào lệnh
            '5m': 4,    # Khung nhỏ - tìm điểm vào lệnh
            '15m': 5,   # Khung trung bình - xác nhận xu hướng
            '30m': 6,   # Khung trung bình - xác nhận xu hướng
            '1h': 7,    # Khung lớn - xác định xu hướng chính
            '4h': 8     # Khung lớn - xác định xu hướng chính
        }
    
    def is_configured(self) -> bool:
        """Kiểm tra xem Telegram đã được cấu hình chưa"""
        return bool(self.tg_token and self.tg_chat_id)
    
    def create_multi_timeframe_chart(self, symbol: str, chart_data: Dict) -> str:
        """
        Tạo chart 7 khung thời gian với MACD
        
        Args:
            symbol: Mã cổ phiếu
            chart_data: Dict chứa dữ liệu cho 7 khung thời gian
            
        Returns:
            Path to saved chart image
        """
        if not chart_data:
            raise ValueError("Chart data is empty")
        
        # Tạo figure với 7 subplots
        fig, axes = plt.subplots(7, 1, figsize=(16, 20))
        fig.suptitle(f'{symbol} - Multi-Timeframe Analysis with MACD', fontsize=16, fontweight='bold')
        
        # Màu sắc cho từng khung thời gian
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8']
        
        for i, tf in enumerate(self.timeframes):
            if tf not in chart_data:
                continue
                
            tf_data = chart_data[tf]
            df = tf_data.get('df')
            macd_data = tf_data.get('macd_data')
            
            if df is None or df.empty:
                continue
            
            # Chuẩn bị dữ liệu
            df_chart = df.copy()
            df_chart.index = pd.to_datetime(df_chart.index)
            
            # Tạo subplot
            ax1 = axes[i]
            ax2 = ax1.twinx()
            
            # Vẽ nến
            mpf.plot(df_chart, type='candle', ax=ax1, volume=False, style='yahoo')
            
            # Vẽ MACD nếu có
            if macd_data and 'macd' in macd_data and 'signal' in macd_data and 'hist' in macd_data:
                # Align MACD data với price data
                common_index = df_chart.index.intersection(pd.Index(macd_data.get('index', [])))
                if len(common_index) > 0:
                    macd_values = macd_data['macd'][:len(common_index)]
                    signal_values = macd_data['signal'][:len(common_index)]
                    hist_values = macd_data['hist'][:len(common_index)]
                    
                    # Vẽ MACD
                    ax2.plot(common_index, macd_values, color='blue', linewidth=1, label='MACD')
                    ax2.plot(common_index, signal_values, color='red', linewidth=1, label='Signal')
                    
                    # Vẽ histogram
                    colors_hist = ['green' if x >= 0 else 'red' for x in hist_values]
                    ax2.bar(common_index, hist_values, color=colors_hist, alpha=0.7, width=0.8)
            
            # Cấu hình subplot
            ax1.set_title(f'{tf} - Weight: {self.tf_weights.get(tf, 1)}', 
                         fontsize=12, fontweight='bold', color=colors[i])
            ax1.set_ylabel('Price ($)', fontsize=10)
            ax2.set_ylabel('MACD', fontsize=10)
            
            # Grid
            ax1.grid(True, alpha=0.3)
            ax2.grid(True, alpha=0.3)
            
            # Legend cho MACD
            if macd_data:
                ax2.legend(loc='upper right', fontsize=8)
        
        # Cấu hình layout
        plt.tight_layout()
        plt.subplots_adjust(top=0.95)
        
        # Tạo file tạm
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            # Lưu chart
            plt.savefig(temp_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            return temp_path
            
        except Exception as e:
            plt.close()
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e
    
    def send_multi_timeframe_chart(self, symbol: str, chart_data: Dict, 
                                 signal_info: Dict = None) -> bool:
        """
        Gửi chart 7 khung thời gian với MACD
        
        Args:
            symbol: Mã cổ phiếu
            chart_data: Dữ liệu cho 7 khung thời gian
            signal_info: Thông tin tín hiệu (nếu có)
            
        Returns:
            True nếu gửi thành công
        """
        if not self.is_configured():
            print("⚠️ Telegram not configured")
            return False
        
        try:
            # Tạo chart
            chart_path = self.create_multi_timeframe_chart(symbol, chart_data)
            
            # Tạo caption
            caption = self._create_multi_timeframe_caption(symbol, signal_info)
            
            # Gửi chart
            success = self._send_photo(chart_path, caption)
            
            # Xóa file tạm
            if os.path.exists(chart_path):
                os.unlink(chart_path)
            
            return success
            
        except Exception as e:
            print(f"❌ Error sending multi-timeframe chart for {symbol}: {e}")
            return False
    
    def _create_multi_timeframe_caption(self, symbol: str, signal_info: Dict = None) -> str:
        """Tạo caption cho multi-timeframe chart"""
        
        # Thời gian hiện tại
        now = datetime.now(timezone.utc)
        us_time = now.astimezone(timezone(timedelta(hours=-5)))  # EST
        vn_time = now.astimezone(timezone(timedelta(hours=7)))   # VN
        
        caption = f"<b>📊 {symbol} - Multi-Timeframe Analysis</b>\n\n"
        
        # Thông tin tín hiệu nếu có
        if signal_info:
            signal_type = signal_info.get('signal_type', 'NEUTRAL')
            score = signal_info.get('score', 0)
            buy_signals = signal_info.get('buy_signals', 0)
            sell_signals = signal_info.get('sell_signals', 0)
            
            signal_emoji = "🟢" if signal_type == "BUY" else "🔴" if signal_type == "SELL" else "⚪"
            signal_text = "MUA" if signal_type == "BUY" else "BÁN" if signal_type == "SELL" else "NEUTRAL"
            
            caption += f"<b>🎯 Signal:</b> {signal_emoji} {signal_text}\n"
            caption += f"<b>📊 Score:</b> {score}\n"
            caption += f"<b>🟢 Buy Signals:</b> {buy_signals}\n"
            caption += f"<b>🔴 Sell Signals:</b> {sell_signals}\n\n"
        
        # Thông tin khung thời gian
        caption += f"<b>⏰ Timeframes:</b>\n"
        for tf in self.timeframes:
            weight = self.tf_weights.get(tf, 1)
            caption += f"   {tf}: Weight {weight}\n"
        
        caption += f"\n<b>📈 MACD Indicators:</b>\n"
        caption += f"   🔵 Blue Line: FMACD (Fast MACD)\n"
        caption += f"   🔴 Red Line: SMACD (Signal MACD)\n"
        caption += f"   🟢/🔴 Bars: Histogram (FMACD - SMACD)\n\n"
        
        caption += f"<b>⏰ Analysis Time:</b>\n"
        caption += f"🇺🇸 US: {us_time.strftime('%Y-%m-%d %H:%M:%S EST')}\n"
        caption += f"🇻🇳 VN: {vn_time.strftime('%Y-%m-%d %H:%M:%S VN')}\n"
        caption += f"🌍 UTC: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        
        caption += "<i>⚠️ Multi-timeframe analysis for reference only</i>"
        
        return caption
    
    def _send_photo(self, photo_path: str, caption: str) -> bool:
        """Gửi ảnh đến Telegram"""
        url = f"https://api.telegram.org/bot{self.tg_token}/sendPhoto"
        
        try:
            with open(photo_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': self.tg_chat_id,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                
                response = requests.post(url, files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    print(f"✅ Multi-timeframe chart sent to Telegram successfully")
                    return True
                else:
                    print(f"❌ Failed to send multi-timeframe chart: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error sending photo: {e}")
            return False
    
    def get_chart_data_for_all_timeframes(self, symbol: str) -> Dict:
        """
        Lấy dữ liệu chart cho tất cả 7 khung thời gian
        
        Args:
            symbol: Mã cổ phiếu
            
        Returns:
            Dict chứa dữ liệu cho 7 khung thời gian
        """
        try:
            from app.db import init_db, SessionLocal
            from sqlalchemy import text
            
            # Initialize database
            init_db(os.getenv("DATABASE_URL"))
            
            # Get session
            session = SessionLocal()
            try:
                # Lấy symbol_id
                symbol_row = session.execute(text("""
                    SELECT id FROM symbols WHERE ticker = :ticker
                """), {'ticker': symbol}).fetchone()
                
                if not symbol_row:
                    return {}
                
                symbol_id = symbol_row[0]
                chart_data = {}
                
                for tf in self.timeframes:
                    # Lấy candles data - tăng limit để đảm bảo có đủ dữ liệu cho MACD
                    candles_query = text("""
                        SELECT ts, open, high, low, close, volume
                        FROM candles_tf
                        WHERE symbol_id = :symbol_id AND timeframe = :timeframe
                        ORDER BY ts DESC
                        LIMIT 200
                    """)
                    
                    candles_rows = session.execute(candles_query, {
                        'symbol_id': symbol_id,
                        'timeframe': tf
                    }).fetchall()
                    
                    if not candles_rows:
                        print(f"⚠️ No candles data for {tf}")
                        continue
                    
                    # Tạo DataFrame
                    df = pd.DataFrame(candles_rows, columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
                    df.set_index('ts', inplace=True)
                    df.sort_index(inplace=True)
                    
                    # Convert to float
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    # Kiểm tra có đủ dữ liệu để tính MACD không (cần ít nhất 26 periods)
                    if len(df) < 26:
                        print(f"⚠️ Not enough data for MACD calculation in {tf}: {len(df)} candles")
                        continue
                    
                    # Lấy MACD data
                    macd_query = text("""
                        SELECT ts, macd, macd_signal, hist
                        FROM indicators_macd
                        WHERE symbol_id = :symbol_id AND timeframe = :timeframe
                        ORDER BY ts DESC
                        LIMIT 200
                    """)
                    
                    macd_rows = session.execute(macd_query, {
                        'symbol_id': symbol_id,
                        'timeframe': tf
                    }).fetchall()
                    
                    macd_data = None
                    if macd_rows:
                        macd_df = pd.DataFrame(macd_rows, columns=['ts', 'macd', 'signal', 'hist'])
                        macd_df.set_index('ts', inplace=True)
                        macd_df.sort_index(inplace=True)
                        
                        # Convert to float
                        for col in ['macd', 'signal', 'hist']:
                            macd_df[col] = pd.to_numeric(macd_df[col], errors='coerce')
                        
                        # Align với candles data
                        common_index = df.index.intersection(macd_df.index)
                        if len(common_index) >= 26:  # Đảm bảo có đủ dữ liệu MACD
                            # Lấy dữ liệu MACD tương ứng với candles
                            macd_aligned = macd_df.loc[common_index]
                            macd_data = {
                                'macd': macd_aligned['macd'].values,
                                'signal': macd_aligned['signal'].values,
                                'hist': macd_aligned['hist'].values,
                                'index': common_index
                            }
                            print(f"✅ {tf}: {len(df)} candles, {len(common_index)} MACD points")
                        else:
                            print(f"⚠️ Not enough MACD data for {tf}: {len(common_index)} points")
                    else:
                        print(f"⚠️ No MACD data for {tf}")
                    
                    # Chỉ thêm vào chart_data nếu có đủ dữ liệu
                    if macd_data is not None:
                        chart_data[tf] = {
                            'df': df,
                            'macd_data': macd_data
                        }
                
                return chart_data
            finally:
                session.close()
                
        except Exception as e:
            print(f"❌ Error getting chart data for all timeframes: {e}")
            return {}

# Global instance
multi_timeframe_chart_service = MultiTimeframeChartService()
