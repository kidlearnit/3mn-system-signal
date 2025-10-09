#!/usr/bin/env python3
"""
Telegram Market Service - Gửi tin nhắn với flag phân biệt thị trường US/VN
"""

import os
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

class TelegramMarketService:
    def __init__(self):
        self.tg_token = os.getenv('TG_TOKEN')
        self.tg_chat_id = os.getenv('TG_CHAT_ID')
        
    def is_configured(self) -> bool:
        """Kiểm tra xem Telegram đã được cấu hình chưa"""
        return bool(self.tg_token and self.tg_chat_id)
    
    def send_trading_signal(self, symbol: str, signal_type: str, score: int, 
                          sig_map: Dict, market_source: str = "US", 
                          exchange: str = "NASDAQ", strategy_id: int = 1):
        """
        Gửi tín hiệu trading với flag thị trường
        
        Args:
            symbol: Mã cổ phiếu (VD: TQQQ, VN30)
            signal_type: Loại tín hiệu (BUY/SELL)
            score: Điểm số tín hiệu
            sig_map: Bản đồ tín hiệu theo timeframe
            market_source: Nguồn thị trường (US/VN)
            exchange: Sàn giao dịch
            strategy_id: ID chiến lược
        """
        if not self.is_configured():
            print("⚠️ Telegram not configured, skipping signal")
            return False
            
        try:
            message = self._create_signal_message(
                symbol, signal_type, score, sig_map, market_source, exchange, strategy_id
            )
            
            success = self._send_telegram_message(message)
            if success:
                print(f"✅ Trading signal sent for {symbol} ({market_source})")
            return success
            
        except Exception as e:
            print(f"❌ Trading signal error for {symbol}: {e}")
            return False
    
    def _create_signal_message(self, symbol: str, signal_type: str, score: int,
                             sig_map: Dict, market_source: str, exchange: str, 
                             strategy_id: int) -> str:
        """Tạo tin nhắn tín hiệu với flag thị trường"""
        
        # Market flags và icons
        market_flags = {
            "US": {"flag": "🇺🇸", "name": "US MARKET", "timezone": "EST"},
            "VN": {"flag": "🇻🇳", "name": "VIETNAM MARKET", "timezone": "VN"}
        }
        
        market_info = market_flags.get(market_source, market_flags["US"])
        
        # Signal emoji và text
        signal_emoji = "🟢" if signal_type == "BUY" else "🔴"
        signal_text = "MUA" if signal_type == "BUY" else "BÁN"
        
        # Header với thông tin thị trường
        header = f"{signal_emoji} *{symbol}* - TÍN HIỆU {signal_text}\n"
        header += f"{market_info['flag']} *{market_info['name']}*\n"
        header += f"📊 Score: {score} | 🟢 Mua: {self._count_signals(sig_map, 'BUY')} | 🔴 Bán: {self._count_signals(sig_map, 'SELL')}\n"
        header += f"🏢 Exchange: {exchange}\n"
        header += f"⏰ {self._get_market_time(market_source)}\n"
        header += "─" * 40 + "\n"
        
        # Chi tiết từng timeframe
        details = []
        for tf_name, data in sig_map.items():
            tf_emoji = "📈" if data.get('signal') == "BUY" else "📉" if data.get('signal') == "SELL" else "➖"
            tf_signal = "MUA" if data.get('signal') == "BUY" else "BÁN" if data.get('signal') == "SELL" else "KHÔNG"
            
            detail_line = (
                f"{tf_emoji} *{tf_name}*: {tf_signal}\n"
                f"   💰 Giá: {self._format_value(data.get('close'), '.2f')}\n"
                f"   📊 MACD: {self._format_value(data.get('macd'), '.3f')}\n"
                f"   📈 Signal: {self._format_value(data.get('signal_line'), '.3f')}\n"
                f"   📉 Hist: {self._format_value(data.get('hist'), '.3f')}"
            )
            
            details.append(detail_line)
        
        detail_str = "\n\n".join(details)
        
        # Footer với thông tin thị trường
        footer = "\n" + "─" * 40 + "\n"
        footer += f"🎯 *Strategy ID:* {strategy_id}\n"
        footer += f"🌍 *Market Source:* {market_info['flag']} {market_source}\n"
        footer += f"⏰ *Timezone:* {market_info['timezone']}\n"
        footer += "📊 *Weighted Scoring System*\n"
        footer += "⚠️ *Disclaimer:* Chỉ là tín hiệu tham khảo, không phải lời khuyên đầu tư"
        
        return header + detail_str + footer
    
    def _count_signals(self, sig_map: Dict, signal_type: str) -> int:
        """Đếm số lượng tín hiệu theo loại"""
        return sum(1 for data in sig_map.values() if data.get('signal') == signal_type)
    
    def _format_value(self, value, format_str: str) -> str:
        """Format giá trị số"""
        if value is None:
            return "N/A"
        try:
            return f"{float(value):{format_str}}"
        except:
            return "N/A"
    
    def _get_market_time(self, market_source: str) -> str:
        """Lấy thời gian theo thị trường"""
        now = pd.Timestamp.now(tz='UTC')
        
        if market_source == "US":
            # US time (EST/EDT)
            us_time = now.tz_convert('US/Eastern')
            return us_time.strftime('%H:%M:%S %d/%m/%Y EST')
        elif market_source == "VN":
            # Vietnam time
            vn_time = now.tz_convert('Asia/Ho_Chi_Minh')
            return vn_time.strftime('%H:%M:%S %d/%m/%Y VN')
        else:
            # UTC time
            return now.strftime('%H:%M:%S %d/%m/%Y UTC')
    
    def _send_telegram_message(self, message: str) -> bool:
        """Gửi tin nhắn đến Telegram"""
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        
        payload = {
            "chat_id": self.tg_chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                print(f"❌ Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Telegram send error: {e}")
            return False
    
    def send_zone_alert(self, symbol: str, zone: str, price: float, 
                       macd: float, market_source: str = "US", 
                       confidence: str = "medium"):
        """
        Gửi cảnh báo zone với flag thị trường
        
        Args:
            symbol: Mã cổ phiếu
            zone: Zone hiện tại
            price: Giá hiện tại
            macd: Giá trị MACD
            market_source: Nguồn thị trường (US/VN)
            confidence: Độ tin cậy (high/medium/low)
        """
        if not self.is_configured():
            print("⚠️ Telegram not configured, skipping zone alert")
            return False
            
        try:
            message = self._create_zone_alert_message(
                symbol, zone, price, macd, market_source, confidence
            )
            
            success = self._send_telegram_message(message)
            if success:
                print(f"✅ Zone alert sent for {symbol} ({market_source})")
            return success
            
        except Exception as e:
            print(f"❌ Zone alert error for {symbol}: {e}")
            return False
    
    def _create_zone_alert_message(self, symbol: str, zone: str, price: float,
                                 macd: float, market_source: str, confidence: str) -> str:
        """Tạo tin nhắn cảnh báo zone"""
        
        # Market flags
        market_flags = {
            "US": {"flag": "🇺🇸", "name": "US MARKET"},
            "VN": {"flag": "🇻🇳", "name": "VIETNAM MARKET"}
        }
        
        market_info = market_flags.get(market_source, market_flags["US"])
        
        # Zone icons
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
        
        # Confidence icons
        confidence_icons = {
            "high": "🎯",
            "medium": "⚠️",
            "low": "❓"
        }
        
        zone_icon = zone_icons.get(zone, "❓")
        confidence_icon = confidence_icons.get(confidence, "❓")
        
        # Tạo message
        message = f"🎯 *ZONE ALERT - {symbol}*\n"
        message += f"{market_info['flag']} *{market_info['name']}*\n\n"
        message += f"🎯 *Zone:* {zone_icon} {zone.upper()}\n"
        message += f"🎯 *Confidence:* {confidence_icon} {confidence.upper()}\n"
        message += f"💰 *Price:* ${price:.2f}\n"
        message += f"📈 *MACD:* {macd:.3f}\n"
        message += f"⏰ *Time:* {self._get_market_time(market_source)}\n\n"
        message += "⚠️ *Zone alert - Chỉ là cảnh báo tham khảo*"
        
        return message

# Global instance
telegram_market_service = TelegramMarketService()
