"""
Telegram Chart Service - Gửi chart nến kèm theo zone alerts
"""
import os
import tempfile
import pandas as pd
import mplfinance as mpf
from datetime import datetime, timezone, timedelta
import requests
from typing import Dict, List, Optional
import numpy as np

class TelegramChartService:
    def __init__(self):
        self.tg_token = os.getenv('TG_TOKEN')
        self.tg_chat_id = os.getenv('TG_CHAT_ID')
    
    def is_configured(self) -> bool:
        """Kiểm tra xem Telegram đã được cấu hình chưa"""
        return bool(self.tg_token and self.tg_chat_id)
    
    def create_candlestick_chart(self, symbol: str, timeframe: str, df: pd.DataFrame, 
                                macd_data: Optional[Dict] = None, zone: str = None) -> str:
        """
        Tạo chart nến với MACD và zone information
        
        Args:
            symbol: Mã cổ phiếu
            timeframe: Khung thời gian
            df: DataFrame chứa OHLCV data
            macd_data: Dict chứa MACD data
            zone: Zone hiện tại
            
        Returns:
            Path to saved chart image
        """
        if df.empty:
            raise ValueError("DataFrame is empty")
        
        # Chuẩn bị dữ liệu
        df_chart = df.copy()
        df_chart.index = pd.to_datetime(df_chart.index)
        
        # Tạo title với zone info
        title = f"{symbol} - {timeframe}"
        if zone:
            zone_icons = {
                "igr": "🚀🔥",
                "greed": "💰🟢", 
                "bull": "🐂📈",
                "pos": "👍🟢",
                "neutral": "⚪️😐",
                "neg": "👎🔻",
                "bear": "🐻📉",
                "fear": "😨🔴",
                "panic": "🆘😱"
            }
            zone_icon = zone_icons.get(zone.lower(), "❓")
            title += f" - {zone_icon} {zone.upper()}"
        
        # Chuẩn bị additional plots
        apds = []
        
        # Thêm MACD nếu có
        if macd_data and 'macd' in macd_data and 'signal' in macd_data and 'hist' in macd_data:
            # Tạo DataFrame cho MACD
            macd_df = pd.DataFrame({
                'macd': macd_data['macd'],
                'signal': macd_data['signal'],
                'hist': macd_data['hist']
            }, index=df_chart.index)
            
            apds.extend([
                mpf.make_addplot(macd_df['macd'], panel=1, color='blue', width=1, title='MACD'),
                mpf.make_addplot(macd_df['signal'], panel=1, color='red', width=1, title='Signal'),
                mpf.make_addplot(macd_df['hist'], panel=1, type='bar', color='green', alpha=0.7, title='Histogram')
            ])
        
        # Tạo file tạm
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            # Vẽ chart
            mpf.plot(
                df_chart,
                type='candle',
                addplot=apds,
                volume=True,
                style='yahoo',
                title=title,
                ylabel='Price ($)',
                ylabel_lower='Volume',
                figsize=(12, 8),
                savefig=dict(
                    fname=temp_path,
                    dpi=150,
                    bbox_inches='tight',
                    facecolor='white'
                )
            )
            
            return temp_path
            
        except Exception as e:
            # Xóa file tạm nếu có lỗi
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e
    
    def send_chart_with_zone_alert(self, symbol: str, timeframe: str, zone_data: Dict, 
                                  price_data: Dict, chart_data: Dict) -> bool:
        """
        Gửi chart nến kèm theo zone alert
        
        Args:
            symbol: Mã cổ phiếu
            timeframe: Khung thời gian
            zone_data: Dữ liệu zone
            price_data: Dữ liệu giá
            chart_data: Dữ liệu để tạo chart
            
        Returns:
            True nếu gửi thành công
        """
        if not self.is_configured():
            print("⚠️ Telegram not configured")
            return False
        
        try:
            # Tạo chart
            chart_path = self.create_candlestick_chart(
                symbol=symbol,
                timeframe=timeframe,
                df=chart_data['df'],
                macd_data=chart_data.get('macd_data'),
                zone=zone_data.get('zone')
            )
            
            # Tạo caption
            caption = self._create_chart_caption(symbol, timeframe, zone_data, price_data)
            
            # Gửi chart
            success = self._send_photo(chart_path, caption)
            
            # Xóa file tạm
            if os.path.exists(chart_path):
                os.unlink(chart_path)
            
            return success
            
        except Exception as e:
            print(f"❌ Error sending chart for {symbol} {timeframe}: {e}")
            return False
    
    def _create_chart_caption(self, symbol: str, timeframe: str, zone_data: Dict, price_data: Dict) -> str:
        """Tạo caption cho chart"""
        zone = zone_data.get('zone', 'unknown')
        zone_icons = {
            "igr": "🚀🔥",
            "greed": "💰🟢", 
            "bull": "🐂📈",
            "pos": "👍🟢",
            "neutral": "⚪️😐",
            "neg": "👎🔻",
            "bear": "🐻📉",
            "fear": "😨🔴",
            "panic": "🆘😱"
        }
        
        zone_icon = zone_icons.get(zone.lower(), "❓")
        
        # Thời gian hiện tại
        now = datetime.now(timezone.utc)
        us_time = now.astimezone(timezone(timedelta(hours=-5)))  # EST
        vn_time = now.astimezone(timezone(timedelta(hours=7)))   # VN
        
        caption = f"<b>📊 {symbol} - {timeframe} Chart</b>\n\n"
        caption += f"<b>🎯 Zone:</b> {zone_icon} {zone.upper()}\n"
        caption += f"<b>💰 Price:</b> ${price_data.get('close', 0):.2f}\n"
        caption += f"<b>📈 High:</b> ${price_data.get('high', 0):.2f}\n"
        caption += f"<b>📉 Low:</b> ${price_data.get('low', 0):.2f}\n"
        caption += f"<b>📊 Volume:</b> {price_data.get('volume', 0):,.0f}\n\n"
        
        if 'fmacd' in zone_data:
            caption += f"<b>📊 FMACD:</b> {zone_data['fmacd']:.3f}\n"
        if 'smacd' in zone_data:
            caption += f"<b>📈 SMACD:</b> {zone_data['smacd']:.3f}\n"
        if 'bars' in zone_data:
            caption += f"<b>📉 Bars:</b> {zone_data['bars']:.3f}\n\n"
        
        caption += f"<b>⏰ Chart Time:</b>\n"
        caption += f"🇺🇸 US: {us_time.strftime('%Y-%m-%d %H:%M:%S EST')}\n"
        caption += f"🇻🇳 VN: {vn_time.strftime('%Y-%m-%d %H:%M:%S VN')}\n"
        caption += f"🌍 UTC: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        
        caption += "<i>⚠️ Chart for reference only - Not investment advice</i>"
        
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
                    print(f"✅ Chart sent to Telegram successfully")
                    return True
                else:
                    print(f"❌ Failed to send chart: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error sending photo: {e}")
            return False
    
    def send_simple_chart(self, symbol: str, timeframe: str, df: pd.DataFrame, 
                         caption: str = "") -> bool:
        """
        Gửi chart đơn giản không có MACD
        
        Args:
            symbol: Mã cổ phiếu
            timeframe: Khung thời gian
            df: DataFrame OHLCV
            caption: Caption cho chart
            
        Returns:
            True nếu gửi thành công
        """
        if not self.is_configured():
            print("⚠️ Telegram not configured")
            return False
        
        try:
            # Tạo chart đơn giản
            chart_path = self.create_candlestick_chart(symbol, timeframe, df)
            
            # Gửi chart
            success = self._send_photo(chart_path, caption)
            
            # Xóa file tạm
            if os.path.exists(chart_path):
                os.unlink(chart_path)
            
            return success
            
        except Exception as e:
            print(f"❌ Error sending simple chart for {symbol} {timeframe}: {e}")
            return False

# Global instance
telegram_chart_service = TelegramChartService()

