#!/usr/bin/env python3
"""
Simple Real Telegram Digest - Sử dụng data thực từ database (basic SMA)
"""

import os
import sys
import time
import logging
from datetime import datetime, timezone
import requests

# Add app to path
sys.path.append('/app')

from app.db import SessionLocal, init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleRealTelegramDigest:
    def __init__(self):
        # Initialize database first
        init_db(os.getenv("DATABASE_URL"))
        
        self.tg_token = os.getenv('TG_TOKEN')
        self.tg_chat_id = os.getenv('TG_CHAT_ID')
        self.interval = int(os.getenv('TELEGRAM_DIGEST_INTERVAL_SECONDS', '300'))  # 5 minutes
        
        # Get symbols from environment
        self.symbols = self._get_symbols_to_monitor()
        self.timeframes = ['1m', '2m', '5m', '15m', '30m', '1h', '4h']
        
        logger.info(f"Simple Real Telegram Digest initialized")
        logger.info(f"TG_TOKEN: {self.tg_token[:20] if self.tg_token else 'NOT_SET'}...")
        logger.info(f"TG_CHAT_ID: {self.tg_chat_id}")
        logger.info(f"Interval: {self.interval} seconds")
        logger.info(f"Monitoring {len(self.symbols)} symbols")
    
    def _get_symbols_to_monitor(self) -> list:
        """Get symbols to monitor from environment"""
        symbols_env = os.getenv('EMAIL_DIGEST_SYMBOLS', '')
        
        if symbols_env:
            symbol_list = [s.strip() for s in symbols_env.split(',')]
        else:
            # Fallback to top 30 VN symbols
            symbol_list = [
                'TPB', 'VCB', 'VGC', 'VHM', 'VIC', 'VJC', 'VNM', 'VRE', 'VPI', 'VPB',
                'VSH', 'VTO', 'VHC', 'VND', 'VOS', 'VSC', 'VSI', 'VTB', 'VTV', 'VWS',
                'VXF', 'VYS', 'VZB', 'VZC', 'VZD', 'VZE', 'VZF', 'VZG', 'VZH', 'VZI'
            ]
        
        return symbol_list[:30]  # Limit to 30 symbols
    
    def is_configured(self) -> bool:
        """Check if Telegram is configured"""
        return bool(self.tg_token and self.tg_chat_id)
    
    def is_market_open(self, exchange: str) -> bool:
        """Check if market is currently open"""
        from datetime import datetime, timezone
        import pytz
        
        now = datetime.now(timezone.utc)
        
        if exchange in ['HOSE', 'HNX', 'UPCOM']:  # Vietnam markets
            # VN market: 9:00-15:00 VN time (UTC+7)
            vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
            vn_time = now.astimezone(vn_tz)
            
            # Check if it's a weekday (Monday=0, Sunday=6)
            if vn_time.weekday() >= 5:  # Weekend
                return False
                
            # Check time (9:00-15:00)
            market_open = vn_time.replace(hour=9, minute=0, second=0, microsecond=0)
            market_close = vn_time.replace(hour=15, minute=0, second=0, microsecond=0)
            
            return market_open <= vn_time <= market_close
            
        elif exchange in ['NASDAQ', 'NYSE']:  # US markets
            # US market: 9:30-16:00 ET (UTC-5/-4)
            et_tz = pytz.timezone('US/Eastern')
            et_time = now.astimezone(et_tz)
            
            # Check if it's a weekday
            if et_time.weekday() >= 5:  # Weekend
                return False
                
            # Check time (9:30-16:00)
            market_open = et_time.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = et_time.replace(hour=16, minute=0, second=0, microsecond=0)
            
            return market_open <= et_time <= market_close
        
        return False
    
    def send_real_message(self) -> bool:
        """Send real message with data from database"""
        if not self.is_configured():
            logger.warning("Telegram not configured")
            return False
        
        try:
            # Get real signals from database
            signals_data = self._get_real_signals()
            
            if not signals_data:
                logger.info("No signals to send")
                return False
            
            message = self._format_telegram_table(signals_data)
            success = self._send_telegram_message(message)
            return success
            
        except Exception as e:
            logger.error(f"Error sending real message: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_real_signals(self) -> list:
        """Get real signals from database"""
        signals_data = []
        
        try:
            with SessionLocal() as db:
                for symbol in self.symbols:
                    # Get symbol info
                    symbol_info = db.execute(
                        "SELECT id, ticker, exchange, company_name FROM symbols WHERE ticker = %s AND active = 1",
                        (symbol,)
                    ).fetchone()
                    
                    if not symbol_info:
                        continue
                    
                    symbol_id, ticker, exchange, company_name = symbol_info
                    
                    # Check if market is open
                    if not self.is_market_open(exchange):
                        continue
                    
                    # Get latest signals for this symbol
                    signals = db.execute(
                        """
                        SELECT s.timeframe, s.signal_type, s.signal_strength, s.current_price, s.ma18, s.ma36, s.ma48, s.ma144, s.created_at
                        FROM sma_signals s
                        WHERE s.symbol_id = %s 
                        AND s.timeframe IN %s
                        AND s.created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                        ORDER BY s.created_at DESC
                        LIMIT 7
                        """,
                        (symbol_id, tuple(self.timeframes))
                    ).fetchall()
                    
                    if signals:
                        # Analyze signals
                        analysis = self._analyze_signals(signals, ticker, company_name, exchange)
                        if analysis:
                            signals_data.append(analysis)
        
        except Exception as e:
            logger.error(f"Error getting real signals: {e}")
        
        # Sort by signal strength
        signals_data.sort(key=lambda x: x['signal_strength'], reverse=True)
        
        return signals_data[:30]  # Top 30
    
    def _analyze_signals(self, signals, ticker, company_name, exchange) -> dict:
        """Analyze signals for a symbol"""
        if not signals:
            return None
        
        # Group signals by type
        confirmed_signals = [s for s in signals if 'confirmed' in s[1]]
        bullish_signals = [s for s in signals if 'bullish' in s[1]]
        bearish_signals = [s for s in signals if 'bearish' in s[1]]
        
        # Calculate overall signal strength
        total_strength = sum(float(s[2] or 0) for s in signals)
        avg_strength = total_strength / len(signals) if signals else 0
        
        # Determine primary signal
        if len(confirmed_signals) >= 2:
            primary_signal = 'CONFIRMED'
        elif len(bullish_signals) > len(bearish_signals):
            primary_signal = 'BULLISH'
        elif len(bearish_signals) > len(bullish_signals):
            primary_signal = 'BEARISH'
        else:
            primary_signal = 'NEUTRAL'
        
        # Get latest price and MA data
        latest_signal = signals[0]
        current_price = float(latest_signal[3] or 0)
        ma18 = float(latest_signal[4] or 0)
        ma36 = float(latest_signal[5] or 0)
        ma48 = float(latest_signal[6] or 0)
        ma144 = float(latest_signal[7] or 0)
        
        # Calculate risk level based on MA spread
        if ma18 > 0 and ma144 > 0:
            ma_spread = abs(ma18 - ma144) / ma144 * 100
            if ma_spread < 2:
                risk = 'LOW'
            elif ma_spread < 5:
                risk = 'MED'
            else:
                risk = 'HIGH'
        else:
            risk = 'MED'
        
        # Generate analysis
        reasoning = self._generate_reasoning(signals, primary_signal)
        
        return {
            'symbol': ticker,
            'company': company_name or ticker,
            'exchange': exchange,
            'signal': primary_signal,
            'confidence': round(avg_strength, 1),
            'risk': risk,
            'rr_ratio': 2.0,  # Default R/R ratio
            'price': current_price,
            'change': 0.0,  # Will be calculated from price data
            'reasoning': reasoning,
            'signal_strength': len(confirmed_signals),
            'timeframe_count': len(signals),
            'ma18': ma18,
            'ma36': ma36,
            'ma48': ma48,
            'ma144': ma144
        }
    
    def _generate_reasoning(self, signals, primary_signal) -> str:
        """Generate reasoning for the signal"""
        confirmed_tf = [s[0] for s in signals if 'confirmed' in s[1]]
        
        if primary_signal == 'CONFIRMED':
            return f"✅ Confirmed: {', '.join(confirmed_tf)} | 🎯 Multi-timeframe"
        elif primary_signal in ['BULLISH', 'BEARISH']:
            return f"📊 Trend alignment | 🎯 {len(signals)} timeframes"
        else:
            return f"⚪ Neutral trend | 📊 {len(signals)} timeframes"
    
    def _format_telegram_table(self, signals_data: list) -> str:
        """Format Telegram message with beautiful table"""
        timestamp = datetime.now().strftime('%H:%M UTC %d/%m')
        
        # Header
        message = f"📊 *SMA TRADING DIGEST* - {timestamp}\n"
        message += f"🎯 {len(signals_data)} Active Signals | 🔄 5min Update\n\n"
        
        # Market status
        vn_open = any(s['exchange'] in ['HOSE', 'HNX', 'UPCOM'] for s in signals_data)
        us_open = any(s['exchange'] in ['NASDAQ', 'NYSE'] for s in signals_data)
        
        message += "🌏 *MARKET STATUS:*\n"
        if vn_open and us_open:
            message += "🇻🇳 VN: ✅ OPEN | 🇺🇸 US: ✅ OPEN\n\n"
        elif vn_open:
            message += "🇻🇳 VN: ✅ OPEN | 🇺🇸 US: ❌ CLOSED\n\n"
        elif us_open:
            message += "🇻🇳 VN: ❌ CLOSED | 🇺🇸 US: ✅ OPEN\n\n"
        else:
            message += "🇻🇳 VN: ❌ CLOSED | 🇺🇸 US: ❌ CLOSED\n\n"
        
        # Main table with colors
        message += "📈 *SIGNALS TABLE:*\n"
        message += "```\n"
        
        # Table header
        message += f"{'#':<2} {'Symbol':<6} {'Signal':<10} {'Conf':<5} {'Risk':<4} {'Price':<8} {'MA18':<8} {'Analysis':<15}\n"
        message += "─" * 70 + "\n"
        
        # Table rows with color indicators
        for i, data in enumerate(signals_data[:30], 1):
            symbol = data['symbol']
            signal = data['signal']
            conf = f"{data['confidence']:.1f}"
            risk = data['risk']
            price = f"{data['price']:.2f}" if data['price'] > 0 else "N/A"
            ma18 = f"{data['ma18']:.2f}" if data['ma18'] > 0 else "N/A"
            analysis = data['reasoning'][:14] + "..." if len(data['reasoning']) > 14 else data['reasoning']
            
            # Color indicators based on signal
            if signal == 'CONFIRMED':
                signal_icon = "🟢"
            elif signal == 'BULLISH':
                signal_icon = "🟡"
            elif signal == 'BEARISH':
                signal_icon = "🔴"
            else:
                signal_icon = "⚪"
            
            # Risk color
            if risk == 'LOW':
                risk_icon = "🟢"
            elif risk == 'MED':
                risk_icon = "🟡"
            else:
                risk_icon = "🔴"
            
            message += f"{i:<2} {symbol:<6} {signal_icon}{signal:<9} {conf:<5} {risk_icon}{risk:<3} {price:<8} {ma18:<8} {analysis:<15}\n"
        
        message += "```\n\n"
        
        # Legend
        message += "🎨 *LEGEND:*\n"
        message += "🟢 CONFIRMED/LOW | 🟡 BULLISH/MED | 🔴 BEARISH/HIGH | ⚪ NEUTRAL\n\n"
        
        # Top 5 detailed analysis
        message += "🔍 *TOP 5 DETAILED ANALYSIS:*\n\n"
        
        for i, data in enumerate(signals_data[:5], 1):
            signal_emoji = "🟢" if data['signal'] == 'CONFIRMED' else "🟡" if data['signal'] == 'BULLISH' else "🔴" if data['signal'] == 'BEARISH' else "⚪"
            risk_emoji = "🟢" if data['risk'] == 'LOW' else "🟡" if data['risk'] == 'MED' else "🔴"
            
            message += f"*{i}. {data['symbol']} - {data['company']}*\n"
            message += f"{signal_emoji} Signal: {data['signal']} | {risk_emoji} Risk: {data['risk']}\n"
            message += f"📊 Confidence: {data['confidence']}/10 | 💰 Price: {data['price']:.2f}\n"
            message += f"📈 MA18: {data['ma18']:.2f} | MA144: {data['ma144']:.2f}\n"
            message += f"🎯 {data['reasoning']}\n\n"
        
        # Trading guidelines
        message += "📱 *TRADING GUIDELINES:*\n"
        message += "• 🟢 CONFIRMED: Strong buy/sell signals\n"
        message += "• 🟡 BULLISH: Moderate buy signals\n"
        message += "• 🔴 BEARISH: Sell signals\n"
        message += "• ⚪ NEUTRAL: Hold positions\n"
        message += "• Use proper position sizing\n"
        message += "• Set stop losses as indicated\n\n"
        
        # Footer
        message += "🔄 *Next update in 5 minutes*\n"
        message += "📊 Enhanced SMA System | Multi-timeframe Analysis"
        
        return message
    
    def _send_telegram_message(self, message: str) -> bool:
        """Send Telegram message"""
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
                logger.info("Telegram message sent successfully")
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return False
    
    def run_loop(self):
        """Run in a loop"""
        logger.info(f"Starting Simple Real Telegram Digest loop; interval={self.interval} seconds")
        
        while True:
            try:
                logger.info("Sending real message...")
                success = self.send_real_message()
                
                if success:
                    logger.info("Real message sent successfully")
                else:
                    logger.info("No signals to send or failed to send")
                
                time.sleep(self.interval)
                
            except KeyboardInterrupt:
                logger.info("Telegram digest loop stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in Telegram digest loop: {e}")
                time.sleep(60)  # Wait 1 minute before retry

def main():
    """Main function"""
    digest = SimpleRealTelegramDigest()
    digest.run_loop()

if __name__ == "__main__":
    main()
