#!/usr/bin/env python3
"""
Telegram Zone Alert Service - Thông báo chi tiết khi khung giờ đi vào zone
"""
import os
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from decimal import Decimal

class TelegramZoneService:
    def __init__(self):
        self.tg_token = os.getenv('TG_TOKEN')
        self.tg_chat_id = os.getenv('TG_CHAT_ID')
        
    def is_configured(self) -> bool:
        """Kiểm tra xem Telegram đã được cấu hình chưa"""
        return bool(self.tg_token and self.tg_chat_id)
    
    def send_zone_alert(self, symbol: str, timeframe: str, zone_data: Dict, price_data: Dict, include_chart: bool = True):
        """Gửi thông báo khi khung giờ đi vào zone"""
        if not self.is_configured():
            print("⚠️ Telegram not configured, skipping zone alert")
            return
            
        try:
            message = self._create_zone_message(symbol, timeframe, zone_data, price_data)
            self._send_telegram_message(message)
            print(f"✅ Zone alert sent for {symbol} {timeframe}")
            
            # Gửi chart nếu được yêu cầu
            if include_chart:
                self._send_zone_chart(symbol, timeframe, zone_data, price_data)
                
        except Exception as e:
            print(f"❌ Zone alert error for {symbol} {timeframe}: {e}")
    
    def _send_zone_chart(self, symbol: str, timeframe: str, zone_data: Dict, price_data: Dict):
        """Gửi chart nến kèm theo zone alert"""
        try:
            from app.services.telegram_chart_service import telegram_chart_service
            
            if not telegram_chart_service.is_configured():
                print("⚠️ Chart service not configured, skipping chart")
                return
            
            # Lấy dữ liệu chart từ database
            chart_data = self._get_chart_data(symbol, timeframe)
            if not chart_data:
                print("⚠️ No chart data available, skipping chart")
                return
            
            # Gửi chart
            success = telegram_chart_service.send_chart_with_zone_alert(
                symbol=symbol,
                timeframe=timeframe,
                zone_data=zone_data,
                price_data=price_data,
                chart_data=chart_data
            )
            
            if success:
                print(f"✅ Zone chart sent for {symbol} {timeframe}")
            else:
                print(f"❌ Failed to send zone chart for {symbol} {timeframe}")
                
        except Exception as e:
            print(f"❌ Zone chart error for {symbol} {timeframe}: {e}")
    
    def _get_chart_data(self, symbol: str, timeframe: str) -> Optional[Dict]:
        """Lấy dữ liệu để tạo chart"""
        try:
            from app.db import init_db, SessionLocal
            from sqlalchemy import text
            import pandas as pd
            
            init_db(os.getenv("DATABASE_URL"))
            
            with SessionLocal() as s:
                # Lấy symbol_id
                symbol_row = s.execute(text("""
                    SELECT id FROM symbols WHERE ticker = :ticker
                """), {'ticker': symbol}).fetchone()
                
                if not symbol_row:
                    return None
                
                symbol_id = symbol_row[0]
                
                # Lấy candles data
                candles_query = text("""
                    SELECT ts, open, high, low, close, volume
                    FROM candles_tf
                    WHERE symbol_id = :symbol_id AND timeframe = :timeframe
                    ORDER BY ts DESC
                    LIMIT 100
                """)
                
                candles_rows = s.execute(candles_query, {
                    'symbol_id': symbol_id,
                    'timeframe': timeframe
                }).fetchall()
                
                if not candles_rows:
                    return None
                
                # Tạo DataFrame
                df = pd.DataFrame(candles_rows, columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
                df.set_index('ts', inplace=True)
                df.sort_index(inplace=True)
                
                # Convert to float
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Lấy MACD data
                macd_query = text("""
                    SELECT ts, macd, macd_signal, hist
                    FROM indicators_macd
                    WHERE symbol_id = :symbol_id AND timeframe = :timeframe
                    ORDER BY ts DESC
                    LIMIT 100
                """)
                
                macd_rows = s.execute(macd_query, {
                    'symbol_id': symbol_id,
                    'timeframe': timeframe
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
                    if len(common_index) > 0:
                        macd_data = {
                            'macd': macd_df.loc[common_index, 'macd'].values,
                            'signal': macd_df.loc[common_index, 'signal'].values,
                            'hist': macd_df.loc[common_index, 'hist'].values
                        }
                
                return {
                    'df': df,
                    'macd_data': macd_data
                }
                
        except Exception as e:
            print(f"❌ Error getting chart data: {e}")
            return None
    
    def send_zone_summary(self, symbol: str, timeframe: str, zone_history: List[Dict]):
        """Gửi tổng hợp các zone đã đi qua trong khung giờ"""
        if not self.is_configured():
            print("⚠️ Telegram not configured, skipping zone summary")
            return
            
        try:
            message = self._create_zone_summary_message(symbol, timeframe, zone_history)
            self._send_telegram_message(message)
            print(f"✅ Zone summary sent for {symbol} {timeframe}")
        except Exception as e:
            print(f"❌ Zone summary error for {symbol} {timeframe}: {e}")
    
    def _create_zone_message(self, symbol: str, timeframe: str, zone_data: Dict, price_data: Dict) -> str:
        """Tạo message chi tiết cho zone alert"""
        
        # Zone icons
        zone_icons = {
            "igr": "🚀🔥",      # Insane Greed
            "greed": "💰🟢",    # Greed
            "bull": "🐂📈",     # Bull
            "pos": "👍🟢",      # Positive
            "neutral": "⚪️😐",  # Neutral
            "neg": "👎🔻",      # Negative
            "bear": "🐻📉",     # Bear
            "fear": "😨🔴",     # Fear
            "panic": "🆘😱"     # Panic
        }
        
        zone = zone_data.get('zone', 'unknown')
        zone_icon = zone_icons.get(zone, "❓")
        
        # Lấy dữ liệu
        close_price = price_data.get('close', 0)
        high_price = price_data.get('high', 0)
        low_price = price_data.get('low', 0)
        volume = price_data.get('volume', 0)
        
        fmacd = zone_data.get('fmacd', 0)
        smacd = zone_data.get('smacd', 0)
        bars = zone_data.get('bars', 0)
        signal_line = zone_data.get('signal_line', 0)
        
        # Tạo message
        message = f"<b>🎯 ZONE ALERT - {symbol}</b>\n"
        message += f"<b>⏰ Timeframe:</b> {timeframe}\n"
        
        # Thời gian hiện tại (khi gửi tin nhắn)
        current_utc = datetime.now(timezone.utc)
        current_us = current_utc.astimezone(timezone(timedelta(hours=-5)))  # EST (UTC-5)
        current_vn = current_utc.astimezone(timezone(timedelta(hours=7)))   # VN (UTC+7)
        
        message += f"<b>📱 Sent Time:</b>\n"
        message += f"   🇺🇸 US: {current_us.strftime('%Y-%m-%d %H:%M:%S EST')}\n"
        message += f"   🇻🇳 VN: {current_vn.strftime('%Y-%m-%d %H:%M:%S VN')}\n"
        message += f"   🌍 UTC: {current_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        
        # Thời gian của nến (khi phân tích)
        try:
            candle_time = price_data.get('candle_time')
            if candle_time:
                if isinstance(candle_time, str):
                    candle_time = datetime.fromisoformat(candle_time.replace('Z', '+00:00'))
                elif candle_time.tzinfo is None:
                    candle_time = candle_time.replace(tzinfo=timezone.utc)
                
                # Chuyển đổi thời gian nến sang các múi giờ
                candle_us = candle_time.astimezone(timezone(timedelta(hours=-5)))  # EST (UTC-5)
                candle_vn = candle_time.astimezone(timezone(timedelta(hours=7)))   # VN (UTC+7)
                
                message += f"<b>🕯️ Market Candle Time:</b>\n"
                message += f"   🇺🇸 US: {candle_us.strftime('%Y-%m-%d %H:%M:%S EST')}\n"
                message += f"   🇻🇳 VN: {candle_vn.strftime('%Y-%m-%d %H:%M:%S VN')}\n"
                message += f"   🌍 UTC: {candle_time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                
                # Tính độ trễ
                delay_minutes = (current_utc - candle_time).total_seconds() / 60
                message += f"<b>⏱️ Data Delay:</b> {delay_minutes:.1f} minutes\n"
            else:
                message += f"<b>🕯️ Market Candle Time:</b> Not available\n"
        except Exception as e:
            message += f"<b>🕯️ Market Candle Time:</b> Error parsing\n"
        
        message += "\n"
        
        message += f"<b>📍 Zone:</b> {zone_icon} <b>{zone.upper()}</b>\n\n"
        
        message += f"<b>💰 Price Data:</b>\n"
        message += f"   • Close: <b>${close_price:.4f}</b>\n"
        message += f"   • High: <b>${high_price:.4f}</b>\n"
        message += f"   • Low: <b>${low_price:.4f}</b>\n"
        message += f"   • Volume: <b>{volume:,.0f}</b>\n\n"
        
        message += f"<b>📊 MACD Indicators:</b>\n"
        message += f"   • Fast MACD: <b>{fmacd:.6f}</b>\n"
        message += f"   • Slow MACD: <b>{smacd:.6f}</b>\n"
        message += f"   • Signal Line: <b>{signal_line:.6f}</b>\n"
        message += f"   • Histogram: <b>{bars:.6f}</b>\n\n"
        
        # Thêm phân tích zone
        message += self._get_zone_analysis(zone, bars)
        
        return message
    
    def _create_zone_summary_message(self, symbol: str, timeframe: str, zone_history: List[Dict]) -> str:
        """Tạo message tổng hợp zone history"""
        
        if not zone_history:
            return f"<b>📊 Zone Summary - {symbol}</b>\n<b>⏰ Timeframe:</b> {timeframe}\n\n❌ No zone data available"
        
        # Đếm số lần vào từng zone
        zone_counts = {}
        for entry in zone_history:
            zone = entry.get('zone', 'unknown')
            zone_counts[zone] = zone_counts.get(zone, 0) + 1
        
        # Zone icons
        zone_icons = {
            "igr": "🚀🔥", "greed": "💰🟢", "bull": "🐂📈", "pos": "👍🟢",
            "neutral": "⚪️😐", "neg": "👎🔻", "bear": "🐻📉", "fear": "😨🔴", "panic": "🆘😱"
        }
        
        message = f"<b>📊 Zone Summary - {symbol}</b>\n"
        message += f"<b>⏰ Timeframe:</b> {timeframe}\n"
        message += f"<b>🕐 Period:</b> {len(zone_history)} entries\n"
        
        # Thời gian hiện tại (khi gửi báo cáo)
        current_utc = datetime.now(timezone.utc)
        current_us = current_utc.astimezone(timezone(timedelta(hours=-5)))  # EST (UTC-5)
        current_vn = current_utc.astimezone(timezone(timedelta(hours=7)))   # VN (UTC+7)
        
        message += f"<b>📱 Generated Time:</b>\n"
        message += f"   🇺🇸 US: {current_us.strftime('%Y-%m-%d %H:%M:%S EST')}\n"
        message += f"   🇻🇳 VN: {current_vn.strftime('%Y-%m-%d %H:%M:%S VN')}\n"
        message += f"   🌍 UTC: {current_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        
        # Thời gian của dữ liệu (từ zone_history)
        if zone_history:
            try:
                # Lấy thời gian đầu và cuối của dữ liệu
                first_entry = zone_history[0]
                last_entry = zone_history[-1]
                
                if 'timestamp' in first_entry and 'timestamp' in last_entry:
                    first_time = first_entry['timestamp']
                    last_time = last_entry['timestamp']
                    
                    if isinstance(first_time, str):
                        first_time = datetime.fromisoformat(first_time.replace('Z', '+00:00'))
                    if isinstance(last_time, str):
                        last_time = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
                    
                    if first_time.tzinfo is None:
                        first_time = first_time.replace(tzinfo=timezone.utc)
                    if last_time.tzinfo is None:
                        last_time = last_time.replace(tzinfo=timezone.utc)
                    
                    # Chuyển đổi sang các múi giờ
                    first_us = first_time.astimezone(timezone(timedelta(hours=-5)))
                    first_vn = first_time.astimezone(timezone(timedelta(hours=7)))
                    last_us = last_time.astimezone(timezone(timedelta(hours=-5)))
                    last_vn = last_time.astimezone(timezone(timedelta(hours=7)))
                    
                    message += f"<b>🕯️ Market Data Range:</b>\n"
                    message += f"   🇺🇸 US: {first_us.strftime('%Y-%m-%d %H:%M')} - {last_us.strftime('%Y-%m-%d %H:%M')}\n"
                    message += f"   🇻🇳 VN: {first_vn.strftime('%Y-%m-%d %H:%M')} - {last_vn.strftime('%Y-%m-%d %H:%M')}\n"
                    message += f"   🌍 UTC: {first_time.strftime('%Y-%m-%d %H:%M')} - {last_time.strftime('%Y-%m-%d %H:%M')}\n"
            except Exception as e:
                message += f"<b>🕯️ Market Data Range:</b> Error parsing\n"
        
        message += "\n"
        
        message += f"<b>🎯 Zone Distribution:</b>\n"
        for zone, count in sorted(zone_counts.items(), key=lambda x: x[1], reverse=True):
            zone_icon = zone_icons.get(zone, "❓")
            percentage = (count / len(zone_history)) * 100
            message += f"   {zone_icon} <b>{zone.upper()}</b>: {count} times ({percentage:.1f}%)\n"
        
        # Thêm thống kê chi tiết
        message += f"\n<b>📈 Statistics:</b>\n"
        message += f"   • Total entries: <b>{len(zone_history)}</b>\n"
        message += f"   • Unique zones: <b>{len(zone_counts)}</b>\n"
        
        # Zone cuối cùng
        if zone_history:
            last_zone = zone_history[-1]
            last_zone_icon = zone_icons.get(last_zone.get('zone', 'unknown'), "❓")
            message += f"   • Current zone: {last_zone_icon} <b>{last_zone.get('zone', 'unknown').upper()}</b>\n"
        
        return message
    
    def _get_zone_analysis(self, zone: str, bars: float) -> str:
        """Phân tích zone và đưa ra nhận xét"""
        analysis = ""
        
        if zone in ["igr", "greed"]:
            analysis = "🚀 <b>BULLISH MOMENTUM:</b> Strong buying pressure detected!"
        elif zone in ["bull", "pos"]:
            analysis = "📈 <b>POSITIVE TREND:</b> Market showing bullish signals"
        elif zone == "neutral":
            analysis = "⚖️ <b>NEUTRAL:</b> Market in consolidation phase"
        elif zone in ["neg", "bear"]:
            analysis = "📉 <b>BEARISH TREND:</b> Market showing bearish signals"
        elif zone in ["fear", "panic"]:
            analysis = "🔴 <b>BEARISH MOMENTUM:</b> Strong selling pressure detected!"
        else:
            analysis = "❓ <b>UNKNOWN ZONE:</b> Zone analysis not available"
        
        # Thêm phân tích histogram
        if bars > 0:
            analysis += "\n📊 <b>Histogram:</b> Above zero line (bullish momentum)"
        elif bars < 0:
            analysis += "\n📊 <b>Histogram:</b> Below zero line (bearish momentum)"
        else:
            analysis += "\n📊 <b>Histogram:</b> At zero line (neutral)"
        
        return analysis
    
    def _send_telegram_message(self, message: str):
        """Gửi message đến Telegram"""
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        
        payload = {
            "chat_id": self.tg_chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"Telegram API error: {response.status_code} - {response.text}")

# Global instance
telegram_zone_service = TelegramZoneService()
