#!/usr/bin/env python3
"""
Vietnamese Telegram Digest - Dự đoán xu hướng bằng tiếng Việt
"""

import os
import sys
import time
import logging
from datetime import datetime, timezone
import requests
from datetime import timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict

# Add app to path for DB access
sys.path.append('/app')
from app.db import SessionLocal, init_db  # type: ignore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VietnameseTelegramDigest:
    def __init__(self):
        self.tg_token = os.getenv('TG_TOKEN')
        self.tg_chat_id = os.getenv('TG_CHAT_ID')
        self.interval = int(os.getenv('TELEGRAM_DIGEST_INTERVAL_SECONDS', '300'))  # 5 minutes
        self.tz_vn = ZoneInfo("Asia/Ho_Chi_Minh")
        # Ensure DB is initialized
        try:
            init_db(os.getenv("DATABASE_URL"))
        except Exception as e:
            logger.warning(f"Could not init DB: {e}")
        
        logger.info(f"Vietnamese Telegram Digest initialized")
        logger.info(f"TG_TOKEN: {self.tg_token[:20] if self.tg_token else 'NOT_SET'}...")
        logger.info(f"TG_CHAT_ID: {self.tg_chat_id}")
        logger.info(f"Interval: {self.interval} seconds")
    
    def is_configured(self) -> bool:
        """Check if Telegram is configured"""
        return bool(self.tg_token and self.tg_chat_id)
    
    def _is_vn_market_open(self) -> bool:
        """Check if Vietnam market is open using local rules.
        Sessions (Mon-Fri): 09:00-11:30 and 13:00-15:00 ICT (Ho Chi Minh time).
        """
        try:
            # Prefer shared utility if available
            from backend.utils.market_time import is_market_open  # type: ignore
            return bool(is_market_open("VN"))
        except Exception:
            # Fallback local check
            now = datetime.now(self.tz_vn)
            if now.weekday() >= 5:  # 5=Sat, 6=Sun
                return False
            t = now.time()
            morning_open = now.replace(hour=9, minute=0, second=0, microsecond=0).time()
            morning_close = now.replace(hour=11, minute=30, second=0, microsecond=0).time()
            afternoon_open = now.replace(hour=13, minute=0, second=0, microsecond=0).time()
            afternoon_close = now.replace(hour=15, minute=0, second=0, microsecond=0).time()
            in_morning = morning_open <= t <= morning_close
            in_afternoon = afternoon_open <= t <= afternoon_close
            return in_morning or in_afternoon
    
    def send_vietnamese_message(self) -> bool:
        """Send Vietnamese message with trend prediction"""
        if not self.is_configured():
            logger.warning("Telegram not configured")
            return False
        
        # Gate by VN market hours
        if not self._is_vn_market_open():
            logger.info("VN market closed, skipping Vietnamese Telegram digest")
            return False
        
        try:
            # Collect realtime data from DB
            symbols_data = self._get_realtime_vn_signals()
            if not symbols_data:
                logger.info("No realtime VN signals available; skipping send")
                return False
            message = self._format_vietnamese_message(symbols_data)
            success = self._send_telegram_message(message)
            return success
            
        except Exception as e:
            logger.error(f"Error sending Vietnamese message: {e}")
            return False
    
    def _get_symbols_vn(self) -> List[str]:
        symbols_env = os.getenv('EMAIL_DIGEST_SYMBOLS', '')
        if symbols_env:
            # Filter to VN tickers by checking presence in DB with VN exchange
            with SessionLocal() as db:
                env_syms = [s.strip() for s in symbols_env.split(',') if s.strip()]
                rows = db.execute(
                    "SELECT ticker FROM symbols WHERE ticker IN %s AND exchange = 'VN' AND active = 1",
                    (tuple(env_syms),)
                ).fetchall()
                return [r[0] for r in rows][:30]
        # Fallback: top active VN symbols
        with SessionLocal() as db:
            rows = db.execute(
                "SELECT ticker FROM symbols WHERE exchange='VN' AND active=1 ORDER BY weight DESC, id ASC LIMIT 30"
            ).fetchall()
            return [r[0] for r in rows]

    def _get_realtime_vn_signals(self) -> List[Dict]:
        """Fetch latest VN signals and map to digest rows."""
        timeframes = ('1m','2m','5m','15m','30m','1h','4h')
        data: List[Dict] = []
        symbols = self._get_symbols_vn()
        if not symbols:
            return data
        with SessionLocal() as db:
            for ticker in symbols:
                # Get symbol info
                row = db.execute(
                    "SELECT id, ticker, company_name FROM symbols WHERE ticker=%s AND exchange='VN' AND active=1",
                    (ticker,)
                ).fetchone()
                if not row:
                    continue
                symbol_id, symbol, company = row
                # Latest price and change from candles_1m
                price_row = db.execute(
                    """
                    SELECT c1.close as price,
                           (c1.close - c2.close)/NULLIF(c2.close,0)*100 as change_pct
                    FROM candles_1m c1
                    LEFT JOIN candles_1m c2 ON c2.symbol_id=c1.symbol_id AND c2.ts=(
                        SELECT MAX(ts) FROM candles_1m WHERE symbol_id=c1.symbol_id AND ts < c1.ts
                    )
                    WHERE c1.symbol_id=%s
                    ORDER BY c1.ts DESC
                    LIMIT 1
                    """,
                    (symbol_id,)
                ).fetchone()
                price = float(price_row[0]) if price_row and price_row[0] is not None else 0.0
                change = float(price_row[1]) if price_row and price_row[1] is not None else 0.0
                # Latest signals from sma_signals
                sig_rows = db.execute(
                    """
                    SELECT timeframe, signal_type, confidence, signal_strength, risk_level, rr_ratio, created_at
                    FROM sma_signals
                    WHERE symbol_id=%s AND timeframe IN %s
                      AND created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                    ORDER BY created_at DESC
                    LIMIT 6
                    """,
                    (symbol_id, timeframes)
                ).fetchall()
                if not sig_rows:
                    continue
                # Pick best signal by confidence then strength
                best = sorted(sig_rows, key=lambda r: ((r[2] or 0), (r[3] or 0)), reverse=True)[0]
                tf, sig_type, conf, strength, risk_level, rr_ratio, _ = best
                # Map to Vietnamese categories
                if sig_type in ("BUY","STRONG_BUY","CONFIRMED_BUY"):
                    signal_label = "CONFIRMED" if (conf or 0) >= 0.7 else "BULLISH"
                elif sig_type in ("SELL","STRONG_SELL","CONFIRMED_SELL"):
                    signal_label = "BEARISH"
                else:
                    signal_label = "NEUTRAL"
                # Confidence scaled to 10
                conf10 = round(float(conf or 0) * 10, 1)
                risk_map = {
                    'low': 'LOW', 'medium': 'MED', 'med': 'MED', 'high': 'HIGH'
                }
                risk = risk_map.get(str(risk_level or '').lower(), 'MED')
                rr = float(rr_ratio or 1.5)
                trend_analysis = self._generate_vietnamese_trend_analysis(signal_label, conf10, risk, change)
                data.append({
                    'symbol': symbol,
                    'company': company or symbol,
                    'signal': signal_label,
                    'confidence': conf10,
                    'risk': risk,
                    'rr_ratio': rr,
                    'price': price,
                    'change': change,
                    'trend_analysis': trend_analysis
                })
        return data
    
    def _generate_vietnamese_trend_analysis(self, signal, confidence, risk, change) -> dict:
        """Generate Vietnamese trend analysis with reasoning"""
        
        # Trend prediction in Vietnamese
        if signal == 'CONFIRMED':
            if confidence > 8.0:
                trend_prediction = "XU HƯỚNG MẠNH"
                trend_explanation = "Tín hiệu rất mạnh, khả năng cao sẽ tiếp tục xu hướng"
            else:
                trend_prediction = "XU HƯỚNG TÍCH CỰC"
                trend_explanation = "Tín hiệu tốt, có khả năng tăng giá trong thời gian tới"
        elif signal == 'BULLISH':
            trend_prediction = "XU HƯỚNG TĂNG"
            trend_explanation = "Có dấu hiệu tích cực, có thể tăng giá nhẹ"
        elif signal == 'BEARISH':
            trend_prediction = "XU HƯỚNG GIẢM"
            trend_explanation = "Có dấu hiệu tiêu cực, có thể giảm giá"
        else:
            trend_prediction = "XU HƯỚNG SIDEWAYS"
            trend_explanation = "Thị trường đi ngang, chờ tín hiệu rõ ràng hơn"
        
        # Risk assessment in Vietnamese
        if risk == 'LOW':
            risk_assessment = "RỦI RO THẤP"
            risk_explanation = "An toàn để đầu tư, biến động ít"
        elif risk == 'MED':
            risk_assessment = "RỦI RO TRUNG BÌNH"
            risk_explanation = "Rủi ro vừa phải, cần theo dõi chặt chẽ"
        else:
            risk_assessment = "RỦI RO CAO"
            risk_explanation = "Biến động mạnh, cần cẩn thận"
        
        # Time horizon
        if confidence > 7.0:
            time_horizon = "1-3 ngày"
        elif confidence > 5.0:
            time_horizon = "3-7 ngày"
        else:
            time_horizon = "1-2 tuần"
        
        # Price movement reasoning
        if abs(change) > 3.0:
            price_reasoning = f"Biến động mạnh ({change:+.2f}%), cần chú ý"
        elif abs(change) > 1.0:
            price_reasoning = f"Biến động vừa phải ({change:+.2f}%)"
        else:
            price_reasoning = f"Biến động nhẹ ({change:+.2f}%), ổn định"
        
        return {
            'trend_prediction': trend_prediction,
            'trend_explanation': trend_explanation,
            'risk_assessment': risk_assessment,
            'risk_explanation': risk_explanation,
            'time_horizon': time_horizon,
            'price_reasoning': price_reasoning,
            'confidence_level': self._get_confidence_level_vietnamese(confidence)
        }
    
    def _get_confidence_level_vietnamese(self, confidence):
        """Get confidence level in Vietnamese"""
        if confidence is None:
            return "THẤP"
        if confidence > 8.0:
            return "RẤT CAO"
        elif confidence > 6.0:
            return "CAO"
        elif confidence > 4.0:
            return "TRUNG BÌNH"
        else:
            return "THẤP"
    
    def _format_vietnamese_message(self, symbols_data: list) -> str:
        """Format Vietnamese Telegram message with trend prediction"""
        timestamp = datetime.now().strftime('%H:%M UTC %d/%m')
        
        # Header
        message = f"📊 *DỰ ĐOÁN XU HƯỚNG THỊ TRƯỜNG* - {timestamp}\n"
        message += f"🎯 {len(symbols_data)} Mã Cổ Phiếu | 🔄 Cập nhật 5 phút\n\n"
        
        # Market status
        message += "🌏 *TÌNH TRẠNG THỊ TRƯỜNG:*\n"
        message += "🇻🇳 VN: ✅ ĐANG MỞ | 🇺🇸 US: ❌ ĐÃ ĐÓNG\n\n"
        
        # Group signals by type for better readability
        confirmed_signals = [s for s in symbols_data if s['signal'] == 'CONFIRMED']
        bullish_signals = [s for s in symbols_data if s['signal'] == 'BULLISH']
        bearish_signals = [s for s in symbols_data if s['signal'] == 'BEARISH']
        neutral_signals = [s for s in symbols_data if s['signal'] == 'NEUTRAL']
        
        # CONFIRMED SIGNALS (Highest Priority)
        if confirmed_signals:
            message += "🟢 *TÍN HIỆU XÁC NHẬN* (Mua/Bán Mạnh)\n"
            for i, data in enumerate(confirmed_signals[:5], 1):
                analysis = data.get('trend_analysis', {})
                if not analysis:
                    continue
                risk_emoji = "🟢" if data['risk'] == 'LOW' else "🟡" if data['risk'] == 'MED' else "🔴"
                
                message += f"*{i}. {data['symbol']} - {data['company']}*\n"
                message += f"📈 Xu hướng: {analysis.get('trend_prediction', 'N/A')}\n"
                # Determine currency based on symbol
                is_vn_stock = data['symbol'].endswith(('VN', 'VNM', 'VCB', 'VIC', 'VHM', 'VJC', 'VRE', 'VPI', 'VPB', 'VSH', 'VTO', 'VHC', 'VND', 'VOS', 'VSC', 'VSI', 'VTB', 'VTV', 'VWS', 'VXF', 'VYS', 'VZB', 'VZC', 'VZD', 'VZE', 'VZF', 'VZG', 'VZH', 'VZI', 'TPB', 'VGC'))
                if is_vn_stock:
                    currency = "₫"
                    price_display = data['price'] * 1000  # Convert to VND (multiply by 1000)
                else:
                    currency = "$"
                    price_display = data['price']
                message += f"💰 Giá: {currency}{price_display:.0f} ({data['change']:+.2f}%) | {risk_emoji} {analysis.get('risk_assessment', 'N/A')}\n"
                message += f"📊 Độ tin cậy: {analysis.get('confidence_level', 'N/A')} ({data['confidence']:.1f}/10)\n"
                message += f"⏰ Thời gian: {analysis.get('time_horizon', 'N/A')}\n"
                message += f"💡 Lý do: {analysis.get('trend_explanation', 'N/A')}\n"
                message += f"⚠️ Rủi ro: {analysis.get('risk_explanation', 'N/A')}\n\n"
        
        # BULLISH SIGNALS
        if bullish_signals:
            message += "🟡 *TÍN HIỆU TĂNG* (Cơ hội Mua)\n"
            for i, data in enumerate(bullish_signals[:5], 1):
                analysis = data.get('trend_analysis', {})
                if not analysis:
                    continue
                risk_emoji = "🟢" if data['risk'] == 'LOW' else "🟡" if data['risk'] == 'MED' else "🔴"
                
                message += f"*{i}. {data['symbol']} - {data['company']}*\n"
                message += f"📈 Xu hướng: {analysis.get('trend_prediction', 'N/A')}\n"
                # Determine currency based on symbol
                is_vn_stock = data['symbol'].endswith(('VN', 'VNM', 'VCB', 'VIC', 'VHM', 'VJC', 'VRE', 'VPI', 'VPB', 'VSH', 'VTO', 'VHC', 'VND', 'VOS', 'VSC', 'VSI', 'VTB', 'VTV', 'VWS', 'VXF', 'VYS', 'VZB', 'VZC', 'VZD', 'VZE', 'VZF', 'VZG', 'VZH', 'VZI', 'TPB', 'VGC'))
                if is_vn_stock:
                    currency = "₫"
                    price_display = data['price'] * 1000  # Convert to VND (multiply by 1000)
                else:
                    currency = "$"
                    price_display = data['price']
                message += f"💰 Giá: {currency}{price_display:.0f} ({data['change']:+.2f}%) | {risk_emoji} {analysis.get('risk_assessment', 'N/A')}\n"
                message += f"📊 Độ tin cậy: {analysis.get('confidence_level', 'N/A')} ({data['confidence']:.1f}/10)\n"
                message += f"💡 Lý do: {analysis.get('trend_explanation', 'N/A')}\n\n"
        
        # BEARISH SIGNALS
        if bearish_signals:
            message += "🔴 *TÍN HIỆU GIẢM* (Cơ hội Bán)\n"
            for i, data in enumerate(bearish_signals[:5], 1):
                analysis = data.get('trend_analysis', {})
                if not analysis:
                    continue
                risk_emoji = "🟢" if data['risk'] == 'LOW' else "🟡" if data['risk'] == 'MED' else "🔴"
                
                message += f"*{i}. {data['symbol']} - {data['company']}*\n"
                message += f"📈 Xu hướng: {analysis.get('trend_prediction', 'N/A')}\n"
                # Determine currency based on symbol
                is_vn_stock = data['symbol'].endswith(('VN', 'VNM', 'VCB', 'VIC', 'VHM', 'VJC', 'VRE', 'VPI', 'VPB', 'VSH', 'VTO', 'VHC', 'VND', 'VOS', 'VSC', 'VSI', 'VTB', 'VTV', 'VWS', 'VXF', 'VYS', 'VZB', 'VZC', 'VZD', 'VZE', 'VZF', 'VZG', 'VZH', 'VZI', 'TPB', 'VGC'))
                if is_vn_stock:
                    currency = "₫"
                    price_display = data['price'] * 1000  # Convert to VND (multiply by 1000)
                else:
                    currency = "$"
                    price_display = data['price']
                message += f"💰 Giá: {currency}{price_display:.0f} ({data['change']:+.2f}%) | {risk_emoji} {analysis.get('risk_assessment', 'N/A')}\n"
                message += f"📊 Độ tin cậy: {analysis.get('confidence_level', 'N/A')} ({data['confidence']:.1f}/10)\n"
                message += f"💡 Lý do: {analysis.get('trend_explanation', 'N/A')}\n\n"
        
        # NEUTRAL SIGNALS (Only show top 3)
        if neutral_signals:
            message += "⚪ *TÍN HIỆU TRUNG TÍNH* (Giữ Vị thế)\n"
            for i, data in enumerate(neutral_signals[:3], 1):
                analysis = data.get('trend_analysis', {})
                if not analysis:
                    continue
                risk_emoji = "🟢" if data['risk'] == 'LOW' else "🟡" if data['risk'] == 'MED' else "🔴"
                
                message += f"*{i}. {data['symbol']} - {data['company']}*\n"
                message += f"📈 Xu hướng: {analysis.get('trend_prediction', 'N/A')}\n"
                # Determine currency based on symbol
                is_vn_stock = data['symbol'].endswith(('VN', 'VNM', 'VCB', 'VIC', 'VHM', 'VJC', 'VRE', 'VPI', 'VPB', 'VSH', 'VTO', 'VHC', 'VND', 'VOS', 'VSC', 'VSI', 'VTB', 'VTV', 'VWS', 'VXF', 'VYS', 'VZB', 'VZC', 'VZD', 'VZE', 'VZF', 'VZG', 'VZH', 'VZI', 'TPB', 'VGC'))
                if is_vn_stock:
                    currency = "₫"
                    price_display = data['price'] * 1000  # Convert to VND (multiply by 1000)
                else:
                    currency = "$"
                    price_display = data['price']
                message += f"💰 Giá: {currency}{price_display:.0f} ({data['change']:+.2f}%) | {risk_emoji} {analysis.get('risk_assessment', 'N/A')}\n"
                message += f"💡 Lý do: {analysis.get('trend_explanation', 'N/A')}\n\n"
        
        # Summary
        message += "📊 *TỔNG KẾT:*\n"
        message += f"🟢 Xác nhận: {len(confirmed_signals)} | 🟡 Tăng: {len(bullish_signals)} | 🔴 Giảm: {len(bearish_signals)} | ⚪ Trung tính: {len(neutral_signals)}\n\n"
        
        # Trading guidelines in Vietnamese
        message += "📱 *HƯỚNG DẪN GIAO DỊCH:*\n"
        message += "🟢 *XÁC NHẬN*: Tín hiệu mạnh - Xác suất cao\n"
        message += "🟡 *TĂNG*: Cơ hội mua tốt - Theo dõi chặt chẽ\n"
        message += "🔴 *GIẢM*: Tín hiệu bán - Cân nhắc bán khống\n"
        message += "⚪ *TRUNG TÍNH*: Giữ vị thế hiện tại - Chờ tín hiệu rõ ràng\n\n"
        
        # Risk management in Vietnamese
        message += "⚠️ *QUẢN LÝ RỦI RO:*\n"
        message += "🟢 THẤP: Giao dịch an toàn | 🟡 TRUNG BÌNH: Rủi ro vừa phải | 🔴 CAO: Rủi ro cao\n"
        message += "• Luôn đặt stop loss\n"
        message += "• Kích thước vị thế dựa trên mức rủi ro\n"
        message += "• Tỷ lệ R/R cho thấy tiềm năng lợi nhuận/rủi ro\n\n"
        
        # Market analysis
        message += "🔍 *PHÂN TÍCH THỊ TRƯỜNG:*\n"
        total_positive = len(confirmed_signals) + len(bullish_signals)
        total_negative = len(bearish_signals)
        
        if total_positive > total_negative:
            message += "📈 Thị trường có xu hướng tích cực\n"
            message += "💡 Nên tập trung vào các mã tăng\n"
        elif total_negative > total_positive:
            message += "📉 Thị trường có xu hướng tiêu cực\n"
            message += "💡 Nên cẩn thận và cân nhắc bán\n"
        else:
            message += "📊 Thị trường đi ngang\n"
            message += "💡 Nên chờ tín hiệu rõ ràng hơn\n"
        
        message += "\n🔄 *Cập nhật tiếp theo trong 5 phút*\n"
        message += "📊 Hệ thống SMA Nâng cao | Phân tích đa khung thời gian"
        
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
                logger.info("Vietnamese Telegram message sent successfully")
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return False
    
    def run_loop(self):
        """Run in a loop"""
        logger.info(f"Starting Vietnamese Telegram Digest loop; interval={self.interval} seconds")
        
        while True:
            try:
                logger.info("Sending Vietnamese message...")
                success = self.send_vietnamese_message()
                
                if success:
                    logger.info("Vietnamese message sent successfully")
                else:
                    logger.error("Failed to send Vietnamese message")
                
                time.sleep(self.interval)
                
            except KeyboardInterrupt:
                logger.info("Telegram digest loop stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in Telegram digest loop: {e}")
                time.sleep(60)  # Wait 1 minute before retry

def main():
    """Main function"""
    digest = VietnameseTelegramDigest()
    digest.run_loop()

if __name__ == "__main__":
    main()
