"""
Telegram Observer Implementation

This module implements the Telegram observer for sending trading signals
to Telegram channels or groups.
"""

import os
import requests
from typing import Optional, Dict, Any
from datetime import datetime

from .base_observer import SignalObserver, SignalEvent
from app.services.debug import debug_helper


class TelegramObserver(SignalObserver):
    """
    Telegram observer for sending trading signals to Telegram.
    
    This observer sends formatted trading signals to a Telegram chat
    using the Telegram Bot API.
    """
    
    def __init__(self, 
                 bot_token: Optional[str] = None,
                 chat_id: Optional[str] = None,
                 name: Optional[str] = None):
        """
        Initialize Telegram observer.
        
        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID
            name: Optional observer name
        """
        super().__init__(name)
        
        self.bot_token = bot_token or os.getenv('TG_TOKEN')
        self.chat_id = chat_id or os.getenv('TG_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        # Default filters
        self.add_filter('min_confidence', 0.7)  # Only send high-confidence signals
        self.add_filter('min_strength', 0.1)    # Only send signals with some strength
    
    def handle_signal(self, event: SignalEvent) -> bool:
        """
        Handle a signal event by sending it to Telegram.
        
        Args:
            event: Signal event to handle
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        try:
            if not self._is_configured():
                debug_helper.log_step("Telegram observer not configured (missing token or chat_id)")
                return False
            
            # Format the message
            message = self._format_signal_message(event.signal)
            
            # Send to Telegram
            success = self._send_telegram_message(message)
            
            if success:
                debug_helper.log_step(
                    f"Sent Telegram signal for {event.signal.symbol}: {event.signal.signal_type}"
                )
            else:
                debug_helper.log_step(
                    f"Failed to send Telegram signal for {event.signal.symbol}"
                )
            
            return success
            
        except Exception as e:
            debug_helper.log_step(f"Error handling Telegram signal for {event.signal.symbol}", error=e)
            return False
    
    def _is_configured(self) -> bool:
        """
        Check if Telegram observer is properly configured.
        
        Returns:
            True if configured, False otherwise
        """
        return bool(self.bot_token and self.chat_id)
    
    def _format_signal_message(self, signal) -> str:
        """
        Format signal data into a Telegram message.
        
        Args:
            signal: Signal object
            
        Returns:
            Formatted message string
        """
        try:
            # Signal emoji and type
            signal_emoji = "🟢" if signal.signal_type == "BUY" else "🔴" if signal.signal_type == "SELL" else "⚪"
            signal_text = "MUA" if signal.signal_type == "BUY" else "BÁN" if signal.signal_type == "SELL" else "HOLD"
            
            # Header
            message = f"{signal_emoji} *{signal.symbol}* - TÍN HIỆU {signal_text}\n"
            message += f"📊 Confidence: {signal.confidence:.2f} | Strength: {signal.strength:.4f}\n"
            message += f"⏰ Timeframe: {signal.timeframe}\n"
            message += f"🎯 Strategy: {signal.strategy_name}\n"
            message += f"🕐 {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}\n"
            message += "─" * 30 + "\n"
            
            # Details
            if signal.details:
                message += "📈 *Chi tiết:*\n"
                
                # MACD details
                if 'macd' in signal.details:
                    message += f"   📊 MACD: {signal.details['macd']:.3f}\n"
                if 'signal' in signal.details:
                    message += f"   📈 Signal: {signal.details['signal']:.3f}\n"
                if 'hist' in signal.details:
                    message += f"   📉 Histogram: {signal.details['hist']:.3f}\n"
                
                # SMA details
                if 'm1' in signal.details:
                    message += f"   📊 M1: {signal.details['m1']:.2f}\n"
                if 'm2' in signal.details:
                    message += f"   📈 M2: {signal.details['m2']:.2f}\n"
                if 'm3' in signal.details:
                    message += f"   📉 M3: {signal.details['m3']:.2f}\n"
                if 'ma144' in signal.details:
                    message += f"   🎯 MA144: {signal.details['ma144']:.2f}\n"
                
                # Price details
                if 'close' in signal.details:
                    message += f"   💰 Giá: {signal.details['close']:.2f}\n"
            
            # Footer
            message += "\n" + "─" * 30 + "\n"
            message += "⚠️ *Lưu ý*: Chỉ là tín hiệu tham khảo, không phải lời khuyên đầu tư"
            
            return message
            
        except Exception as e:
            debug_helper.log_step(f"Error formatting Telegram message: {e}")
            return f"Signal: {signal.symbol} - {signal.signal_type} (Confidence: {signal.confidence:.2f})"
    
    def _send_telegram_message(self, message: str) -> bool:
        """
        Send message to Telegram.
        
        Args:
            message: Message to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return True
            else:
                debug_helper.log_step(f"Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            debug_helper.log_step(f"Telegram request error: {e}")
            return False
        except Exception as e:
            debug_helper.log_step(f"Telegram send error: {e}")
            return False
    
    def set_bot_token(self, bot_token: str) -> None:
        """
        Set Telegram bot token.
        
        Args:
            bot_token: Telegram bot token
        """
        self.bot_token = bot_token
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
    
    def set_chat_id(self, chat_id: str) -> None:
        """
        Set Telegram chat ID.
        
        Args:
            chat_id: Telegram chat ID
        """
        self.chat_id = chat_id
    
    def test_connection(self) -> bool:
        """
        Test Telegram connection.
        
        Returns:
            True if connection is working, False otherwise
        """
        try:
            if not self._is_configured():
                return False
            
            test_message = "🧪 Test message from trading system"
            return self._send_telegram_message(test_message)
            
        except Exception as e:
            debug_helper.log_step(f"Telegram connection test failed: {e}")
            return False


class TelegramMarketObserver(TelegramObserver):
    """
    Enhanced Telegram observer with market-specific formatting.
    
    This observer provides enhanced formatting for different markets
    and includes additional market context.
    """
    
    def __init__(self, 
                 bot_token: Optional[str] = None,
                 chat_id: Optional[str] = None,
                 market: str = "US",
                 name: Optional[str] = None):
        """
        Initialize Telegram market observer.
        
        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID
            market: Market type ("US", "VN", etc.)
            name: Optional observer name
        """
        super().__init__(bot_token, chat_id, name)
        self.market = market
    
    def _format_signal_message(self, signal) -> str:
        """
        Format signal with market-specific information.
        
        Args:
            signal: Signal object
            
        Returns:
            Formatted message string
        """
        try:
            # Market-specific header
            market_emoji = "🇺🇸" if self.market == "US" else "🇻🇳" if self.market == "VN" else "🌍"
            market_name = "US Market" if self.market == "US" else "VN Market" if self.market == "VN" else "Global Market"
            
            # Signal emoji and type
            signal_emoji = "🟢" if signal.signal_type == "BUY" else "🔴" if signal.signal_type == "SELL" else "⚪"
            signal_text = "MUA" if signal.signal_type == "BUY" else "BÁN" if signal.signal_type == "SELL" else "HOLD"
            
            # Header with market info
            message = f"{market_emoji} *{market_name}*\n"
            message += f"{signal_emoji} *{signal.symbol}* - TÍN HIỆU {signal_text}\n"
            message += f"📊 Confidence: {signal.confidence:.2f} | Strength: {signal.strength:.4f}\n"
            message += f"⏰ Timeframe: {signal.timeframe}\n"
            message += f"🎯 Strategy: {signal.strategy_name}\n"
            message += f"🕐 {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}\n"
            message += "─" * 30 + "\n"
            
            # Market-specific details
            if self.market == "US":
                message += "🇺🇸 *US Market Analysis:*\n"
            elif self.market == "VN":
                message += "🇻🇳 *VN Market Analysis:*\n"
            
            # Add signal details
            if signal.details:
                message += "📈 *Chi tiết:*\n"
                
                # Add relevant details based on strategy
                for key, value in signal.details.items():
                    if key not in ['strategy', 'strategy_name']:
                        if isinstance(value, (int, float)):
                            message += f"   📊 {key}: {value:.3f}\n"
                        else:
                            message += f"   📊 {key}: {value}\n"
            
            # Footer with market-specific note
            message += "\n" + "─" * 30 + "\n"
            if self.market == "US":
                message += "⚠️ *Lưu ý*: Tín hiệu thị trường Mỹ, cần xem xét múi giờ và thanh khoản"
            elif self.market == "VN":
                message += "⚠️ *Lưu ý*: Tín hiệu thị trường Việt Nam, cần xem xét thanh khoản và spread"
            else:
                message += "⚠️ *Lưu ý*: Chỉ là tín hiệu tham khảo, không phải lời khuyên đầu tư"
            
            return message
            
        except Exception as e:
            debug_helper.log_step(f"Error formatting market Telegram message: {e}")
            return super()._format_signal_message(signal)
