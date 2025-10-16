#!/usr/bin/env python3
"""
Market Signal Monitor - Sử dụng Hybrid Signal Engine để monitor thị trường
Gửi tín hiệu từng mã riêng lẻ vào Telegram khi thị trường mở cửa
"""

import logging
import asyncio
from datetime import datetime, time
from typing import Dict, List, Optional, Any
import pytz
from sqlalchemy import text

from .hybrid_signal_engine import hybrid_signal_engine
from .sma_telegram_service import SMATelegramService
from ..db import init_db
import os

logger = logging.getLogger(__name__)

class MarketSignalMonitor:
    """Monitor tín hiệu thị trường và gửi từng mã riêng lẻ"""
    
    def __init__(self):
        # Initialize database
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            init_db(database_url)
            # Import SessionLocal after init_db
            from ..db import SessionLocal
            self.SessionLocal = SessionLocal
        
        self.hybrid_engine = hybrid_signal_engine
        self.telegram_service = SMATelegramService()
        # Load config from environment
        self.tg_token = os.getenv('TG_TOKEN')
        self.tg_chat_id = os.getenv('TG_CHAT_ID')
        
        # Cấu hình thời gian thị trường
        self.market_schedules = {
            'VN': {
                'timezone': 'Asia/Ho_Chi_Minh',
                'morning_open': time(9, 0),   # 9:00 AM
                'morning_close': time(11, 30), # 11:30 AM
                'afternoon_open': time(13, 0), # 1:00 PM
                'afternoon_close': time(15, 0), # 3:00 PM
                'weekdays': [0, 1, 2, 3, 4]  # Monday to Friday
            },
            'US': {
                'timezone': 'America/New_York',
                'open': time(9, 30),   # 9:30 AM
                'close': time(16, 0),  # 4:00 PM
                'weekdays': [0, 1, 2, 3, 4]  # Monday to Friday
            }
        }
        
        # Cache để tránh gửi tín hiệu trùng lặp
        self.signal_cache = {}
        self.last_signal_time = {}
        
    def is_market_open(self, market: str) -> bool:
        """Kiểm tra thị trường có đang mở cửa không"""
        try:
            market_config = self.market_schedules.get(market)
            if not market_config:
                return False
            
            # Lấy thời gian hiện tại theo timezone của thị trường
            tz = pytz.timezone(market_config['timezone'])
            now = datetime.now(tz)
            current_time = now.time()
            current_weekday = now.weekday()
            
            # Kiểm tra ngày trong tuần
            if current_weekday not in market_config['weekdays']:
                return False
            
            # Kiểm tra thời gian mở cửa
            if market == 'VN':
                # Thị trường VN có 2 phiên
                morning_open = market_config['morning_open']
                morning_close = market_config['morning_close']
                afternoon_open = market_config['afternoon_open']
                afternoon_close = market_config['afternoon_close']
                
                return ((morning_open <= current_time <= morning_close) or 
                       (afternoon_open <= current_time <= afternoon_close))
            
            elif market == 'US':
                # Thị trường US có 1 phiên
                market_open = market_config['open']
                market_close = market_config['close']
                
                return market_open <= current_time <= market_close
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking market status for {market}: {e}")
            return False
    
    def get_active_symbols(self, market: str) -> List[Dict[str, Any]]:
        """Lấy danh sách symbols đang hoạt động cho thị trường"""
        try:
            # Map market to exchange
            market_to_exchange = {
                'VN': 'HOSE',
                'US': 'NASDAQ'
            }
            exchange = market_to_exchange.get(market, market)
            
            with self.SessionLocal() as s:
                query = text("""
                    SELECT id, ticker, exchange, company_name, sector
                    FROM symbols 
                    WHERE active = 1 AND exchange = :exchange
                    ORDER BY ticker
                """)
                
                result = s.execute(query, {'exchange': exchange})
                symbols = []
                
                for row in result:
                    symbols.append({
                        'id': row.id,
                        'ticker': row.ticker,
                        'exchange': row.exchange,
                        'company_name': row.company_name,
                        'sector': row.sector
                    })
                
                logger.info(f"Found {len(symbols)} active symbols for {market} market")
                return symbols
                
        except Exception as e:
            logger.error(f"Error getting active symbols for {market}: {e}")
            return []
    
    def should_send_signal(self, symbol_id: int, signal_type: str, timeframe: str) -> bool:
        """Kiểm tra có nên gửi tín hiệu không (tránh spam)"""
        try:
            # Tạo key unique cho signal
            signal_key = f"{symbol_id}_{signal_type}_{timeframe}"
            current_time = datetime.now()
            
            # Kiểm tra cache
            if signal_key in self.signal_cache:
                last_sent_time = self.signal_cache[signal_key]
                time_diff = (current_time - last_sent_time).total_seconds()
                
                # Chỉ gửi lại sau ít nhất 30 phút
                if time_diff < 1800:  # 30 minutes
                    return False
            
            # Cập nhật cache
            self.signal_cache[signal_key] = current_time
            return True
            
        except Exception as e:
            logger.error(f"Error checking signal cache: {e}")
            return True  # Gửi nếu có lỗi
    
    def format_signal_message(self, symbol_data: Dict, signal_result: Dict) -> str:
        """Format tin nhắn tín hiệu cho Telegram"""
        try:
            ticker = symbol_data['ticker']
            company = symbol_data.get('company_name', 'N/A')
            sector = symbol_data.get('sector', 'N/A')
            exchange = symbol_data.get('exchange', 'N/A')
            
            # Thông tin tín hiệu
            hybrid_signal = signal_result.get('hybrid_signal', 'UNKNOWN')
            direction = signal_result.get('hybrid_direction', 'NEUTRAL')
            strength = signal_result.get('hybrid_strength', 0.0)
            confidence = signal_result.get('confidence', 0.0)
            timeframe = signal_result.get('timeframe', 'N/A')
            
            # Thông tin chi tiết
            sma_signal = signal_result.get('sma_signal', {})
            macd_signal = signal_result.get('macd_signal', {})
            
            sma_direction = sma_signal.get('direction', 'NEUTRAL')
            macd_direction = macd_signal.get('direction', 'NEUTRAL')
            
            # Lấy cấu hình thresholds
            thresholds_info = self._get_thresholds_info(ticker, timeframe)
            
            # Tính độ chính xác dự kiến
            accuracy_info = self._calculate_expected_accuracy(confidence, hybrid_signal)
            
            # Emoji cho direction
            direction_emoji = {
                'BUY': '🟢',
                'SELL': '🔴', 
                'NEUTRAL': '⚪',
                'STRONG_BUY': '🟢💪',
                'STRONG_SELL': '🔴💪',
                'WEAK_BUY': '🟡',
                'WEAK_SELL': '🟠'
            }
            
            emoji = direction_emoji.get(hybrid_signal, '⚪')
            
            # Format tin nhắn với cấu hình và độ chính xác
            message = f"""
{emoji} **TÍN HIỆU GIAO DỊCH**

📈 **Mã cổ phiếu:** {ticker}
🏢 **Công ty:** {company}
🏭 **Ngành:** {sector}
🌏 **Sàn:** {exchange}
⏰ **Timeframe:** {timeframe}

🎯 **Tín hiệu Hybrid:**
• Loại: {hybrid_signal.replace('_', ' ').upper()}
• Hướng: {direction}
• Độ mạnh: {strength:.2f}
• Độ tin cậy: {confidence:.2f}

📊 **Chi tiết chỉ báo:**
• SMA: {sma_direction}
• MACD: {macd_direction}

⚙️ **Cấu hình Thresholds:**
{thresholds_info}

📈 **Độ chính xác dự kiến:**
{accuracy_info}

⏰ **Thời gian:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            """.strip()
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting signal message: {e}")
            return f"Tín hiệu cho {symbol_data.get('ticker', 'N/A')}: {signal_result.get('hybrid_signal', 'UNKNOWN')}"
    
    def _get_thresholds_info(self, ticker: str, timeframe: str) -> str:
        """Lấy thông tin cấu hình thresholds"""
        try:
            # Load cấu hình từ file YAML
            import yaml
            import os
            
            config_path = f"config/strategies/symbols/{ticker}.yaml"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                if 'indicators' in config and 'macd' in config['indicators']:
                    macd_config = config['indicators']['macd']
                    if 'thresholds' in macd_config and timeframe in macd_config['thresholds']:
                        thresholds = macd_config['thresholds'][timeframe]
                        return f"• MACD Bull: {thresholds.get('bull', 'N/A')}\n• MACD Bear: {thresholds.get('bear', 'N/A')}"
            
            # Fallback to default thresholds
            default_thresholds = {
                '1m': {'bull': 0.12, 'bear': -0.12},
                '2m': {'bull': 0.20, 'bear': -0.20},
                '5m': {'bull': 0.30, 'bear': -0.30},
                '15m': {'bull': 0.45, 'bear': -0.45},
                '30m': {'bull': 0.65, 'bear': -0.65},
                '1h': {'bull': 0.85, 'bear': -0.85},
                '4h': {'bull': 1.25, 'bear': -1.25}
            }
            
            if timeframe in default_thresholds:
                thresholds = default_thresholds[timeframe]
                return f"• MACD Bull: {thresholds['bull']}\n• MACD Bear: {thresholds['bear']} (Default)"
            
            return "• Cấu hình: Default thresholds"
            
        except Exception as e:
            logger.error(f"Error getting thresholds info: {e}")
            return "• Cấu hình: Error loading"
    
    def _calculate_expected_accuracy(self, confidence: float, signal_type: str) -> str:
        """Tính độ chính xác dự kiến"""
        try:
            # Base accuracy từ confidence
            base_accuracy = confidence * 100
            
            # Bonus accuracy dựa trên loại signal
            signal_bonus = {
                'STRONG_BUY': 5.0,
                'STRONG_SELL': 5.0,
                'BUY': 2.0,
                'SELL': 2.0,
                'WEAK_BUY': -3.0,
                'WEAK_SELL': -3.0,
                'NEUTRAL': 0.0
            }
            
            bonus = signal_bonus.get(signal_type, 0.0)
            expected_accuracy = min(95.0, max(50.0, base_accuracy + bonus))
            
            # Đánh giá mức độ tin cậy
            if expected_accuracy >= 80:
                reliability = "🟢 Cao"
            elif expected_accuracy >= 70:
                reliability = "🟡 Trung bình"
            else:
                reliability = "🔴 Thấp"
            
            return f"• Dự kiến: {expected_accuracy:.1f}%\n• Độ tin cậy: {reliability}\n• Loại: {signal_type.replace('_', ' ').title()}"
            
        except Exception as e:
            logger.error(f"Error calculating expected accuracy: {e}")
            return f"• Dự kiến: {confidence*100:.1f}%\n• Độ tin cậy: 🟡 Trung bình"
    
    async def process_symbol_signal(self, symbol_data: Dict[str, Any], timeframe: str = '5m') -> bool:
        """Xử lý tín hiệu cho một symbol cụ thể"""
        try:
            symbol_id = symbol_data['id']
            ticker = symbol_data['ticker']
            
            logger.info(f"Processing signal for {ticker} ({timeframe})")
            
            # Lấy tín hiệu hybrid
            signal_result = self.hybrid_engine.evaluate_hybrid_signal(
                symbol_id=symbol_id,
                ticker=ticker,
                exchange=symbol_data['exchange'],
                timeframe=timeframe
            )
            
            # Kiểm tra có tín hiệu đáng kể không
            hybrid_signal = signal_result.get('hybrid_signal', 'NEUTRAL')
            confidence = signal_result.get('confidence', 0.0)
            
            # Chỉ gửi tín hiệu có độ tin cậy cao
            if confidence < 0.6:
                logger.debug(f"Low confidence signal for {ticker}: {confidence:.2f}")
                return False
            
            # Kiểm tra có nên gửi tín hiệu không
            if not self.should_send_signal(symbol_id, hybrid_signal, timeframe):
                logger.debug(f"Signal already sent recently for {ticker}")
                return False
            
            # Format và gửi tin nhắn
            message = self.format_signal_message(symbol_data, signal_result)
            
            # Gửi tin nhắn Telegram
            success = self.telegram_service._send_telegram_message(message)
            
            if success:
                logger.info(f"✅ Signal sent for {ticker}: {hybrid_signal} (confidence: {confidence:.2f})")
                return True
            else:
                logger.error(f"❌ Failed to send signal for {ticker}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing signal for {symbol_data.get('ticker', 'N/A')}: {e}")
            return False
    
    async def monitor_market_signals(self, market: str = 'VN', timeframes: List[str] = None):
        """Monitor tín hiệu cho toàn bộ thị trường"""
        try:
            if timeframes is None:
                timeframes = ['5m', '15m', '30m', '1h']
            
            logger.info(f"Starting market signal monitoring for {market}")
            
            # Kiểm tra thị trường có mở cửa không
            if not self.is_market_open(market):
                logger.info(f"Market {market} is closed, skipping monitoring")
                return
            
            # Lấy danh sách symbols
            symbols = self.get_active_symbols(market)
            if not symbols:
                logger.warning(f"No active symbols found for {market}")
                return
            
            logger.info(f"Monitoring {len(symbols)} symbols for {market} market")
            
            # Xử lý từng symbol
            processed_count = 0
            signal_count = 0
            
            for symbol_data in symbols:
                try:
                    # Xử lý cho timeframe chính (5m)
                    success = await self.process_symbol_signal(symbol_data, '5m')
                    if success:
                        signal_count += 1
                    
                    processed_count += 1
                    
                    # Delay nhỏ giữa các symbol để tránh spam
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing symbol {symbol_data.get('ticker', 'N/A')}: {e}")
                    continue
            
            logger.info(f"Market monitoring completed: {processed_count} symbols processed, {signal_count} signals sent")
            
        except Exception as e:
            logger.error(f"Error in market signal monitoring: {e}")
    
    async def run_continuous_monitoring(self, market: str = 'VN', interval_minutes: int = 5):
        """Chạy monitoring liên tục"""
        logger.info(f"Starting continuous monitoring for {market} market (interval: {interval_minutes} minutes)")
        
        while True:
            try:
                # Kiểm tra thị trường có mở cửa không
                if self.is_market_open(market):
                    await self.monitor_market_signals(market)
                else:
                    logger.debug(f"Market {market} is closed, waiting...")
                
                # Chờ interval
                await asyncio.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(60)  # Chờ 1 phút trước khi thử lại

# Global instance
market_signal_monitor = MarketSignalMonitor()
