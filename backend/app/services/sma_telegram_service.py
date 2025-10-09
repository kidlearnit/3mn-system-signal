#!/usr/bin/env python3
"""
SMA Telegram Service - Gửi tin nhắn SMA signals với flag thị trường
"""

import os
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List
from app.services.sma_signal_engine import SMASignalType
from app.services.sma_chart_service import sma_chart_service

class SMATelegramService:
    def __init__(self):
        self.tg_token = os.getenv('TG_TOKEN')
        self.tg_chat_id = os.getenv('TG_CHAT_ID')
        
    def is_configured(self) -> bool:
        """Kiểm tra xem Telegram đã được cấu hình chưa"""
        return bool(self.tg_token and self.tg_chat_id)
    
    def send_sma_signal(self, symbol: str, exchange: str, timeframe: str, signal_data: Dict, is_test: bool = False):
        """
        Gửi SMA signal với flag thị trường
        
        Args:
            symbol: Mã cổ phiếu (VD: TQQQ, VN30)
            exchange: Sàn giao dịch
            timeframe: Timeframe của signal
            signal_data: Dict chứa signal information
            is_test: Cờ TEST để phân biệt test vs production
        """
        if not self.is_configured():
            print("⚠️ Telegram not configured, skipping SMA signal")
            return False
            
        try:
            # Extract data from signal_data
            signal_type_str = signal_data.get('signal_type', 'neutral')
            signal_direction = signal_data.get('signal_direction', 'HOLD')
            signal_strength = signal_data.get('signal_strength', 0.0)
            
            # Determine market source
            market_source = "VN" if exchange in ("HOSE", "HNX", "UPCOM") else "US"
            
            message = self._create_sma_signal_message(
                symbol, signal_type_str, signal_direction, signal_strength, 
                signal_data, market_source, exchange, timeframe, is_test
            )
            
            success = self._send_telegram_message(message)
            if success:
                test_flag = " [TEST]" if is_test else ""
                print(f"✅ SMA signal sent for {symbol} ({market_source}) - {signal_type_str}{test_flag}")
            return success
            
        except Exception as e:
            print(f"❌ SMA signal error for {symbol}: {e}")
            return False
    
    def send_sma_triple_signal(self, symbol: str, signal_type: SMASignalType,
                              ma_structures: Dict[str, Dict], market_source: str = "US",
                              exchange: str = "NASDAQ"):
        """
        Gửi Triple SMA signal (1D1, 1D2, 1D5 đều confirmed)
        
        Args:
            symbol: Mã cổ phiếu
            signal_type: Triple Bullish hoặc Triple Bearish
            ma_structures: Dict {timeframe: ma_structure}
            market_source: Nguồn thị trường
            exchange: Sàn giao dịch
        """
        if not self.is_configured():
            print("⚠️ Telegram not configured, skipping Triple SMA signal")
            return False
            
        try:
            message = self._create_triple_sma_message(
                symbol, signal_type, ma_structures, market_source, exchange
            )
            
            success = self._send_telegram_message(message)
            if success:
                print(f"✅ Triple SMA signal sent for {symbol} ({market_source}) - {signal_type.value}")
            return success
            
        except Exception as e:
            print(f"❌ Triple SMA signal error for {symbol}: {e}")
            return False
    
    def _create_sma_signal_message(self, symbol: str, signal_type_str: str, 
                                  signal_direction: str, signal_strength: float,
                                  signal_data: Dict, market_source: str, 
                                  exchange: str, timeframe: str, is_test: bool = False) -> str:
        """Tạo tin nhắn SMA signal"""
        
        # Market flags và icons
        market_flags = {
            "US": {"flag": "🇺🇸", "name": "US MARKET", "timezone": "EST"},
            "VN": {"flag": "🇻🇳", "name": "VIETNAM MARKET", "timezone": "VN"}
        }
        
        market_info = market_flags.get(market_source, market_flags["US"])
        
        # Signal icons và text
        signal_icons = {
            "local_bullish_broken": "🟡",
            "local_bullish": "🟢",
            "confirmed_bullish": "🟢✅",
            "local_bearish_broken": "🟡",
            "local_bearish": "🔴",
            "confirmed_bearish": "🔴✅",
            "neutral": "⚪",
            "triple_bullish": "🚀🔥",
            "triple_bearish": "🆘😱"
        }
        
        signal_texts = {
            "local_bullish_broken": "LOCAL BULLISH BROKEN",
            "local_bullish": "LOCAL BULLISH",
            "confirmed_bullish": "CONFIRMED BULLISH",
            "local_bearish_broken": "LOCAL BEARISH BROKEN",
            "local_bearish": "LOCAL BEARISH",
            "confirmed_bearish": "CONFIRMED BEARISH",
            "neutral": "NEUTRAL",
            "triple_bullish": "TRIPLE BULLISH",
            "triple_bearish": "TRIPLE BEARISH"
        }
        
        signal_icon = signal_icons.get(signal_type_str, "❓")
        signal_text = signal_texts.get(signal_type_str, "UNKNOWN")
        
        # Timeframe category
        tf_category = self._get_timeframe_category(timeframe)
        
        # Test flag
        test_flag = "🧪 *[TEST MODE]*\n" if is_test else ""
        
        # Header
        header = f"{signal_icon} *{symbol}* - SMA {signal_text}\n"
        header += f"{market_info['flag']} *{market_info['name']}*\n"
        header += test_flag
        header += f"📊 Timeframe: {timeframe} ({tf_category})\n"
        header += f"🏢 Exchange: {exchange}\n"
        header += f"⏰ {self._get_market_time(market_source)}\n"
        header += "─" * 40 + "\n"
        
        # MA Structure details
        details = []
        if 'close' in signal_data:
            details.append(f"💰 *Current Price:* {signal_data['close']:.2f}")
        if 'm1' in signal_data:
            details.append(f"📈 *MA18 (M1):* {signal_data['m1']:.2f}")
        if 'm2' in signal_data:
            details.append(f"📊 *MA36 (M2):* {signal_data['m2']:.2f}")
        if 'm3' in signal_data:
            details.append(f"📉 *MA48 (M3):* {signal_data['m3']:.2f}")
        if 'ma144' in signal_data:
            details.append(f"🎯 *MA144:* {signal_data['ma144']:.2f}")
        if 'avg_m1_m2_m3' in signal_data:
            details.append(f"⚖️ *Avg(M1+M2+M3):* {signal_data['avg_m1_m2_m3']:.2f}")
        
        detail_str = "\n".join(details)
        
        # Analysis
        analysis = self._get_signal_analysis(signal_type_str, signal_data)
        
        # Footer
        footer = "\n" + "─" * 40 + "\n"
        footer += f"🎯 *Signal Type:* {signal_type_str}\n"
        footer += f"🌍 *Market Source:* {market_info['flag']} {market_source}\n"
        footer += f"⏰ *Timezone:* {market_info['timezone']}\n"
        footer += "📊 *SMA Strategy System*\n"
        footer += "⚠️ *Disclaimer:* Chỉ là tín hiệu tham khảo, không phải lời khuyên đầu tư"
        
        return header + detail_str + "\n\n" + analysis + footer
    
    def _create_triple_sma_message(self, symbol: str, signal_type: SMASignalType,
                                  ma_structures: Dict[str, Dict], market_source: str,
                                  exchange: str) -> str:
        """Tạo tin nhắn Triple SMA signal"""
        
        # Market flags
        market_flags = {
            "US": {"flag": "🇺🇸", "name": "US MARKET", "timezone": "EST"},
            "VN": {"flag": "🇻🇳", "name": "VIETNAM MARKET", "timezone": "VN"}
        }
        
        market_info = market_flags.get(market_source, market_flags["US"])
        
        # Signal icons
        signal_icons = {
            SMASignalType.TRIPLE_BULLISH: "🚀🔥",
            SMASignalType.TRIPLE_BEARISH: "🆘😱"
        }
        
        signal_texts = {
            SMASignalType.TRIPLE_BULLISH: "TRIPLE BULLISH",
            SMASignalType.TRIPLE_BEARISH: "TRIPLE BEARISH"
        }
        
        signal_icon = signal_icons.get(signal_type, "❓")
        signal_text = signal_texts.get(signal_type, "UNKNOWN")
        
        # Header
        header = f"{signal_icon} *{symbol}* - {signal_text}\n"
        header += f"{market_info['flag']} *{market_info['name']}*\n"
        header += f"🏢 Exchange: {exchange}\n"
        header += f"⏰ {self._get_market_time(market_source)}\n"
        header += "─" * 40 + "\n"
        
        # Triple confirmation details
        details = []
        details.append("🎯 *TRIPLE CONFIRMATION:*")
        details.append("1D1Min + 1D2Min + 1D5Min đều Confirmed")
        details.append("")
        
        # Timeframe details
        for tf in ['1D1Min', '1D2Min', '1D5Min']:
            if tf in ma_structures:
                ma = ma_structures[tf]
                details.append(f"📊 *{tf}:*")
                if 'cp' in ma:
                    details.append(f"   💰 Price: {ma['cp']:.2f}")
                if 'avg_m1_m2_m3' in ma and 'ma144' in ma:
                    details.append(f"   ⚖️ Avg vs MA144: {ma['avg_m1_m2_m3']:.2f} vs {ma['ma144']:.2f}")
                details.append("")
        
        detail_str = "\n".join(details)
        
        # Analysis
        analysis = self._get_triple_signal_analysis(signal_type)
        
        # Footer
        footer = "\n" + "─" * 40 + "\n"
        footer += f"🎯 *Signal Type:* {signal_type.value}\n"
        footer += f"🌍 *Market Source:* {market_info['flag']} {market_source}\n"
        footer += f"⏰ *Timezone:* {market_info['timezone']}\n"
        footer += "📊 *SMA Triple Confirmation System*\n"
        footer += "🚀 *HIGH CONFIDENCE SIGNAL*\n"
        footer += "⚠️ *Disclaimer:* Chỉ là tín hiệu tham khảo, không phải lời khuyên đầu tư"
        
        return header + detail_str + analysis + footer
    
    def _get_signal_analysis(self, signal_type_str: str, signal_data: Dict) -> str:
        """Phân tích signal và đưa ra nhận xét"""
        analysis = ""
        
        if signal_type_str == "local_bullish_broken":
            analysis = "🟡 *LOCAL BULLISH BROKEN:* Giá phá vỡ cấu trúc tăng cục bộ\n"
            analysis += "💡 *Action:* Chuẩn bị cho xu hướng tăng ngắn hạn"
        elif signal_type_str == "local_bullish":
            analysis = "🟢 *LOCAL BULLISH:* Xác nhận xu hướng tăng cục bộ\n"
            analysis += "💡 *Action:* Có thể bắt đầu LONG position"
        elif signal_type_str == "confirmed_bullish":
            analysis = "🟢✅ *CONFIRMED BULLISH:* Xác nhận xu hướng tăng mạnh\n"
            analysis += "💡 *Action:* Strong LONG signal với multi-timeframe confirmation"
        elif signal_type_str == "local_bearish_broken":
            analysis = "🟡 *LOCAL BEARISH BROKEN:* Giá phá vỡ cấu trúc giảm cục bộ\n"
            analysis += "💡 *Action:* Chuẩn bị cho xu hướng giảm ngắn hạn"
        elif signal_type_str == "local_bearish":
            analysis = "🔴 *LOCAL BEARISH:* Xác nhận xu hướng giảm cục bộ\n"
            analysis += "💡 *Action:* Có thể bắt đầu SHORT position"
        elif signal_type_str == "confirmed_bearish":
            analysis = "🔴✅ *CONFIRMED BEARISH:* Xác nhận xu hướng giảm mạnh\n"
            analysis += "💡 *Action:* Strong SHORT signal với multi-timeframe confirmation"
        elif signal_type_str == "triple_bullish":
            analysis = "🚀🔥 *TRIPLE BULLISH:* Tín hiệu tăng mạnh từ 3 khung thời gian SHORT\n"
            analysis += "💡 *Action:* HIGH CONFIDENCE LONG signal - Best entry point"
        elif signal_type_str == "triple_bearish":
            analysis = "🆘😱 *TRIPLE BEARISH:* Tín hiệu giảm mạnh từ 3 khung thời gian SHORT\n"
            analysis += "💡 *Action:* HIGH CONFIDENCE SHORT signal - Best entry point"
        elif signal_type_str == "neutral":
            analysis = "⚪ *NEUTRAL:* Thị trường đang sideway\n"
            analysis += "💡 *Action:* Chờ tín hiệu rõ ràng hơn"
        else:
            analysis = "❓ *UNKNOWN SIGNAL:* Cần phân tích thêm"
        
        # Thêm phân tích MA structure
        if 'avg_m1_m2_m3' in signal_data and 'ma144' in signal_data:
            avg = signal_data['avg_m1_m2_m3']
            ma144 = signal_data['ma144']
            
            if avg > ma144:
                analysis += "\n📊 *MA Analysis:* Avg(M1+M2+M3) > MA144 (Bullish momentum)"
            elif avg < ma144:
                analysis += "\n📊 *MA Analysis:* Avg(M1+M2+M3) < MA144 (Bearish momentum)"
            else:
                analysis += "\n📊 *MA Analysis:* Avg(M1+M2+M3) ≈ MA144 (Neutral)"
        
        return analysis
    
    def _get_triple_signal_analysis(self, signal_type: SMASignalType) -> str:
        """Phân tích Triple signal"""
        if signal_type == SMASignalType.TRIPLE_BULLISH:
            analysis = "🚀🔥 *TRIPLE BULLISH ANALYSIS:*\n"
            analysis += "✅ 1D1Min: Confirmed Bullish\n"
            analysis += "✅ 1D2Min: Confirmed Bullish\n"
            analysis += "✅ 1D5Min: Confirmed Bullish\n"
            analysis += "💡 *Action:* HIGH CONFIDENCE LONG signal\n"
            analysis += "🎯 *Target:* Ride the strong bullish momentum"
        elif signal_type == SMASignalType.TRIPLE_BEARISH:
            analysis = "🆘😱 *TRIPLE BEARISH ANALYSIS:*\n"
            analysis += "✅ 1D1Min: Confirmed Bearish\n"
            analysis += "✅ 1D2Min: Confirmed Bearish\n"
            analysis += "✅ 1D5Min: Confirmed Bearish\n"
            analysis += "💡 *Action:* HIGH CONFIDENCE SHORT signal\n"
            analysis += "🎯 *Target:* Ride the strong bearish momentum"
        else:
            analysis = "❓ *UNKNOWN TRIPLE SIGNAL:* Cần phân tích thêm"
        
        return analysis
    
    def _get_timeframe_category(self, timeframe: str) -> str:
        """Lấy category của timeframe"""
        tf_categories = {
            '1m': 'SHORT',
            '2m': 'SHORT', 
            '5m': 'SHORT',
            '15m': 'CORE',
            '30m': 'CORE',
            '1h': 'CORE',
            '4h': 'LONG'
        }
        
        # Handle different timeframe formats
        if '1D1' in timeframe or timeframe == '1m':
            return 'SHORT'
        elif '1D2' in timeframe or timeframe == '2m':
            return 'SHORT'
        elif '1D5' in timeframe or timeframe == '5m':
            return 'SHORT'
        elif '1D15Min' in timeframe or timeframe == '15m':
            return 'CORE'
        elif '1D30Min' in timeframe or timeframe == '30m':
            return 'CORE'
        elif '1D1hr' in timeframe or timeframe == '1h':
            return 'CORE'
        elif '1D4hr' in timeframe or timeframe == '4h':
            return 'LONG'
        else:
            return tf_categories.get(timeframe, 'UNKNOWN')
    
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
        
        # Escape special characters for Markdown
        escaped_message = message.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('.', '\\.').replace('!', '\\!')
        
        payload = {
            "chat_id": self.tg_chat_id,
            "text": escaped_message,
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

# Global instance
sma_telegram_service = SMATelegramService()
