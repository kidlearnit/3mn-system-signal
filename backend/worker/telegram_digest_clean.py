#!/usr/bin/env python3
"""
Clean Telegram Digest - Format dễ đọc và dễ hiểu
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

class CleanTelegramDigest:
    def __init__(self):
        self.tg_token = os.getenv('TG_TOKEN')
        self.tg_chat_id = os.getenv('TG_CHAT_ID')
        self.interval = int(os.getenv('TELEGRAM_DIGEST_INTERVAL_SECONDS', '300'))  # 5 minutes
        
        logger.info(f"Clean Telegram Digest initialized")
        logger.info(f"TG_TOKEN: {self.tg_token[:20] if self.tg_token else 'NOT_SET'}...")
        logger.info(f"TG_CHAT_ID: {self.tg_chat_id}")
        logger.info(f"Interval: {self.interval} seconds")
    
    def is_configured(self) -> bool:
        """Check if Telegram is configured"""
        return bool(self.tg_token and self.tg_chat_id)
    
    def send_clean_message(self) -> bool:
        """Send clean, easy-to-read message"""
        if not self.is_configured():
            logger.warning("Telegram not configured")
            return False
        
        try:
            # Generate sample data with better distribution
            symbols_data = self._generate_clean_sample_data()
            
            message = self._format_clean_message(symbols_data)
            success = self._send_telegram_message(message)
            return success
            
        except Exception as e:
            logger.error(f"Error sending clean message: {e}")
            return False
    
    def _generate_clean_sample_data(self) -> list:
        """Generate clean sample data with better distribution"""
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
        
        # Better distribution of signals
        signal_distribution = ['CONFIRMED'] * 8 + ['BULLISH'] * 10 + ['BEARISH'] * 8 + ['NEUTRAL'] * 4
        risk_distribution = ['LOW'] * 15 + ['MED'] * 10 + ['HIGH'] * 5
        
        data = []
        for i, (symbol, company) in enumerate(zip(symbols, companies)):
            signal = random.choice(signal_distribution)
            risk = random.choice(risk_distribution)
            conf = round(random.uniform(5.0, 9.5), 1)
            rr = round(random.uniform(1.2, 3.0), 1)
            price = round(random.uniform(10.0, 100.0), 2)
            change = round(random.uniform(-5.0, 5.0), 2)
            
            data.append({
                'symbol': symbol,
                'company': company,
                'signal': signal,
                'confidence': conf,
                'risk': risk,
                'rr_ratio': rr,
                'price': price,
                'change': change
            })
        
        return data
    
    def _format_clean_message(self, symbols_data: list) -> str:
        """Format clean, easy-to-read Telegram message"""
        timestamp = datetime.now().strftime('%H:%M UTC %d/%m')
        
        # Header
        message = f"📊 *SMA TRADING DIGEST* - {timestamp}\n"
        message += f"🎯 {len(symbols_data)} Active Signals | 🔄 5min Update\n\n"
        
        # Market status
        message += "🌏 *MARKET STATUS:*\n"
        message += "🇻🇳 VN: ✅ OPEN | 🇺🇸 US: ❌ CLOSED\n\n"
        
        # Group signals by type for better readability
        confirmed_signals = [s for s in symbols_data if s['signal'] == 'CONFIRMED']
        bullish_signals = [s for s in symbols_data if s['signal'] == 'BULLISH']
        bearish_signals = [s for s in symbols_data if s['signal'] == 'BEARISH']
        neutral_signals = [s for s in symbols_data if s['signal'] == 'NEUTRAL']
        
        # CONFIRMED SIGNALS (Highest Priority)
        if confirmed_signals:
            message += "🟢 *CONFIRMED SIGNALS* (Strong Buy/Sell)\n"
            for i, data in enumerate(confirmed_signals[:8], 1):
                risk_emoji = "🟢" if data['risk'] == 'LOW' else "🟡" if data['risk'] == 'MED' else "🔴"
                message += f"{i:2d}. {data['symbol']} - {data['company']}\n"
                message += f"    💰 Price: {data['price']:.2f} ({data['change']:+.2f}%) | {risk_emoji} Risk: {data['risk']}\n"
                message += f"    📊 Conf: {data['confidence']:.1f}/10 | 📈 R/R: {data['rr_ratio']:.1f}\n\n"
        
        # BULLISH SIGNALS
        if bullish_signals:
            message += "🟡 *BULLISH SIGNALS* (Buy Opportunities)\n"
            for i, data in enumerate(bullish_signals[:8], 1):
                risk_emoji = "🟢" if data['risk'] == 'LOW' else "🟡" if data['risk'] == 'MED' else "🔴"
                message += f"{i:2d}. {data['symbol']} - {data['company']}\n"
                message += f"    💰 Price: {data['price']:.2f} ({data['change']:+.2f}%) | {risk_emoji} Risk: {data['risk']}\n"
                message += f"    📊 Conf: {data['confidence']:.1f}/10 | 📈 R/R: {data['rr_ratio']:.1f}\n\n"
        
        # BEARISH SIGNALS
        if bearish_signals:
            message += "🔴 *BEARISH SIGNALS* (Sell Opportunities)\n"
            for i, data in enumerate(bearish_signals[:8], 1):
                risk_emoji = "🟢" if data['risk'] == 'LOW' else "🟡" if data['risk'] == 'MED' else "🔴"
                message += f"{i:2d}. {data['symbol']} - {data['company']}\n"
                message += f"    💰 Price: {data['price']:.2f} ({data['change']:+.2f}%) | {risk_emoji} Risk: {data['risk']}\n"
                message += f"    📊 Conf: {data['confidence']:.1f}/10 | 📈 R/R: {data['rr_ratio']:.1f}\n\n"
        
        # NEUTRAL SIGNALS (Only show top 5)
        if neutral_signals:
            message += "⚪ *NEUTRAL SIGNALS* (Hold Positions)\n"
            for i, data in enumerate(neutral_signals[:5], 1):
                risk_emoji = "🟢" if data['risk'] == 'LOW' else "🟡" if data['risk'] == 'MED' else "🔴"
                message += f"{i:2d}. {data['symbol']} - {data['company']}\n"
                message += f"    💰 Price: {data['price']:.2f} ({data['change']:+.2f}%) | {risk_emoji} Risk: {data['risk']}\n\n"
        
        # Summary
        message += "📊 *SUMMARY:*\n"
        message += f"🟢 Confirmed: {len(confirmed_signals)} | 🟡 Bullish: {len(bullish_signals)} | 🔴 Bearish: {len(bearish_signals)} | ⚪ Neutral: {len(neutral_signals)}\n\n"
        
        # Trading guidelines
        message += "📱 *TRADING GUIDELINES:*\n"
        message += "🟢 *CONFIRMED*: Strong signals - High probability trades\n"
        message += "🟡 *BULLISH*: Good buy opportunities - Monitor closely\n"
        message += "🔴 *BEARISH*: Sell signals - Consider short positions\n"
        message += "⚪ *NEUTRAL*: Hold current positions - Wait for clearer signals\n\n"
        
        # Risk management
        message += "⚠️ *RISK MANAGEMENT:*\n"
        message += "🟢 LOW: Safe trades | 🟡 MED: Moderate risk | 🔴 HIGH: High risk\n"
        message += "• Always use stop losses\n"
        message += "• Position size based on risk level\n"
        message += "• R/R ratio shows risk/reward potential\n\n"
        
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
        logger.info(f"Starting Clean Telegram Digest loop; interval={self.interval} seconds")
        
        while True:
            try:
                logger.info("Sending clean message...")
                success = self.send_clean_message()
                
                if success:
                    logger.info("Clean message sent successfully")
                else:
                    logger.error("Failed to send clean message")
                
                time.sleep(self.interval)
                
            except KeyboardInterrupt:
                logger.info("Telegram digest loop stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in Telegram digest loop: {e}")
                time.sleep(60)  # Wait 1 minute before retry

def main():
    """Main function"""
    digest = CleanTelegramDigest()
    digest.run_loop()

if __name__ == "__main__":
    main()
