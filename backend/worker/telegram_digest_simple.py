#!/usr/bin/env python3
"""
Simple Telegram Digest - Test version
"""

import os
import sys
import time
import logging
from datetime import datetime, timezone
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleTelegramDigest:
    def __init__(self):
        self.tg_token = os.getenv('TG_TOKEN')
        self.tg_chat_id = os.getenv('TG_CHAT_ID')
        self.interval = int(os.getenv('TELEGRAM_DIGEST_INTERVAL_SECONDS', '300'))  # 5 minutes
        
        logger.info(f"Simple Telegram Digest initialized")
        logger.info(f"TG_TOKEN: {self.tg_token[:20] if self.tg_token else 'NOT_SET'}...")
        logger.info(f"TG_CHAT_ID: {self.tg_chat_id}")
        logger.info(f"Interval: {self.interval} seconds")
    
    def is_configured(self) -> bool:
        """Check if Telegram is configured"""
        return bool(self.tg_token and self.tg_chat_id)
    
    def send_test_message(self) -> bool:
        """Send a test message with 30 symbols"""
        if not self.is_configured():
            logger.warning("Telegram not configured")
            return False
        
        try:
            # Generate 30 sample symbols with different signals
            symbols_data = self._generate_sample_symbols()
            
            message = self._format_telegram_table(symbols_data)
            success = self._send_telegram_message(message)
            return success
            
        except Exception as e:
            logger.error(f"Error sending test message: {e}")
            return False
    
    def _generate_sample_symbols(self) -> list:
        """Generate 30 sample symbols with different signals"""
        import random
        
        symbols = [
            'TPB', 'VCB', 'VGC', 'VHM', 'VIC', 'VJC', 'VNM', 'VRE', 'VPI', 'VPB',
            'VSH', 'VTO', 'VHC', 'VND', 'VOS', 'VSC', 'VSI', 'VTB', 'VTV', 'VWS',
            'VXF', 'VYS', 'VZB', 'VZC', 'VZD', 'VZE', 'VZF', 'VZG', 'VZH', 'VZI'
        ]
        
        companies = [
            'Tien Phong Bank', 'Vietcombank', 'VietinBank', 'Vinhomes', 'Vingroup',
            'VietJet Air', 'Vinamilk', 'Vinhomes Retail', 'PetroVietnam', 'VPBank',
            'Vincom Retail', 'Viettel', 'Vinhomes Healthcare', 'VNDirect', 'VOS',
            'VSC', 'VSI', 'VTB', 'VTV', 'VWS', 'VXF', 'VYS', 'VZB', 'VZC', 'VZD',
            'VZE', 'VZF', 'VZG', 'VZH', 'VZI'
        ]
        
        signals = ['CONFIRMED', 'BULLISH', 'BEARISH', 'NEUTRAL']
        risks = ['LOW', 'MED', 'HIGH']
        
        data = []
        for i, (symbol, company) in enumerate(zip(symbols, companies)):
            signal = random.choice(signals)
            risk = random.choice(risks)
            conf = round(random.uniform(5.0, 9.5), 1)
            rr = round(random.uniform(1.2, 3.0), 1)
            price = round(random.uniform(10.0, 100.0), 2)
            
            data.append({
                'symbol': symbol,
                'company': company,
                'signal': signal,
                'confidence': conf,
                'risk': risk,
                'rr_ratio': rr,
                'price': price,
                'change': round(random.uniform(-5.0, 5.0), 2)
            })
        
        return data
    
    def _format_telegram_table(self, symbols_data: list) -> str:
        """Format Telegram message with beautiful table"""
        timestamp = datetime.now().strftime('%H:%M UTC %d/%m')
        
        # Header
        message = f"📊 *SMA TRADING DIGEST* - {timestamp}\n"
        message += f"🎯 {len(symbols_data)} Active Signals | 🔄 5min Update\n\n"
        
        # Market status
        message += "🌏 *MARKET STATUS:*\n"
        message += "🇻🇳 VN: ✅ OPEN | 🇺🇸 US: ❌ CLOSED\n\n"
        
        # Main table with colors
        message += "📈 *SIGNALS TABLE:*\n"
        message += "```\n"
        
        # Table header
        message += f"{'#':<2} {'Symbol':<6} {'Signal':<10} {'Conf':<5} {'Risk':<4} {'R/R':<4} {'Price':<8} {'Change':<7}\n"
        message += "─" * 60 + "\n"
        
        # Table rows with color indicators
        for i, data in enumerate(symbols_data[:30], 1):
            symbol = data['symbol']
            signal = data['signal']
            conf = f"{data['confidence']:.1f}"
            risk = data['risk']
            rr = f"{data['rr_ratio']:.1f}"
            price = f"{data['price']:.2f}"
            change = f"{data['change']:+.2f}%"
            
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
            
            message += f"{i:<2} {symbol:<6} {signal_icon}{signal:<9} {conf:<5} {risk_icon}{risk:<3} {rr:<4} {price:<8} {change:<7}\n"
        
        message += "```\n\n"
        
        # Legend
        message += "🎨 *LEGEND:*\n"
        message += "🟢 CONFIRMED/LOW | 🟡 BULLISH/MED | 🔴 BEARISH/HIGH | ⚪ NEUTRAL\n\n"
        
        # Top 5 detailed analysis
        message += "🔍 *TOP 5 DETAILED ANALYSIS:*\n\n"
        
        for i, data in enumerate(symbols_data[:5], 1):
            signal_emoji = "🟢" if data['signal'] == 'CONFIRMED' else "🟡" if data['signal'] == 'BULLISH' else "🔴" if data['signal'] == 'BEARISH' else "⚪"
            risk_emoji = "🟢" if data['risk'] == 'LOW' else "🟡" if data['risk'] == 'MED' else "🔴"
            
            message += f"*{i}. {data['symbol']} - {data['company']}*\n"
            message += f"{signal_emoji} Signal: {data['signal']} | {risk_emoji} Risk: {data['risk']}\n"
            message += f"📊 Confidence: {data['confidence']}/10 | 💰 Price: {data['price']:.2f} ({data['change']:+.2f}%)\n"
            message += f"📈 R/R Ratio: {data['rr_ratio']:.1f} | 🎯 Multi-timeframe analysis\n\n"
        
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
        logger.info(f"Starting Simple Telegram Digest loop; interval={self.interval} seconds")
        
        while True:
            try:
                logger.info("Sending test message...")
                success = self.send_test_message()
                
                if success:
                    logger.info("Test message sent successfully")
                else:
                    logger.error("Failed to send test message")
                
                time.sleep(self.interval)
                
            except KeyboardInterrupt:
                logger.info("Telegram digest loop stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in Telegram digest loop: {e}")
                time.sleep(60)  # Wait 1 minute before retry

def main():
    """Main function"""
    digest = SimpleTelegramDigest()
    digest.run_loop()

if __name__ == "__main__":
    main()
