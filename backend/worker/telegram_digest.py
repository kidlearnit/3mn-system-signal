#!/usr/bin/env python3
"""
Telegram Digest Service - Gửi tín hiệu SMA tổng hợp qua Telegram
Tương tự Email Digest nhưng format phù hợp cho Telegram
"""

import os
import sys
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
import pandas as pd

# Add app to path
sys.path.append('/app')

from app.db import SessionLocal, init_db
from app.services.enhanced_signal_engine import EnhancedSignalEngine
from app.services.sma_telegram_service import sma_telegram_service
# Import market time function directly
def is_market_open(exchange: str) -> bool:
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramDigest:
    def __init__(self):
        # Initialize database first
        init_db(os.getenv("DATABASE_URL"))
        
        self.enhanced_engine = EnhancedSignalEngine()
        self.telegram_service = sma_telegram_service
        
        # Configuration from environment
        self.symbols = self._get_symbols_to_monitor()
        self.timeframes = os.getenv('EMAIL_DIGEST_TIMEFRAMES', '1m,2m,5m,15m,30m,1h,4h').split(',')
        self.limit = int(os.getenv('EMAIL_DIGEST_LIMIT', '55'))
        self.interval = int(os.getenv('TELEGRAM_DIGEST_INTERVAL_SECONDS', '300'))  # 5 minutes
        
        logger.info(f"Telegram Digest initialized: {len(self.symbols)} symbols, {len(self.timeframes)} timeframes")
    
    def _get_symbols_to_monitor(self) -> List[Dict]:
        """Get symbols to monitor from environment or database"""
        symbols_env = os.getenv('EMAIL_DIGEST_SYMBOLS', '')
        
        if symbols_env:
            # Parse from environment variable
            symbol_list = [s.strip() for s in symbols_env.split(',')]
        else:
            # Fallback to top active symbols from database
            symbol_list = self._get_top_active_symbols()
        
        # Get symbol details from database
        symbols = []
        with SessionLocal() as db:
            for ticker in symbol_list:
                symbol = db.execute(
                    "SELECT id, ticker, exchange, company_name FROM symbols WHERE ticker = %s AND active = 1",
                    (ticker,)
                ).fetchone()
                
                if symbol:
                    symbols.append({
                        'id': symbol[0],
                        'ticker': symbol[1], 
                        'exchange': symbol[2],
                        'company_name': symbol[3] or ticker
                    })
        
        return symbols[:self.limit]
    
    def _get_top_active_symbols(self) -> List[str]:
        """Get top active symbols from database"""
        with SessionLocal() as db:
            result = db.execute(
                "SELECT ticker FROM symbols WHERE active = 1 ORDER BY weight DESC LIMIT %s",
                (self.limit,)
            ).fetchall()
            return [row[0] for row in result]
    
    def run_telegram_digest(self) -> bool:
        """Run telegram digest once"""
        try:
            logger.info("Starting Telegram Digest...")
            
            # Check if any monitored market is open
            markets_open = []
            for symbol in self.symbols:
                exchange = symbol['exchange']
                if is_market_open(exchange):
                    markets_open.append(exchange)
            
            if not markets_open:
                logger.info("No monitored markets are open, skipping Telegram digest")
                return False
            
            logger.info(f"Markets open: {set(markets_open)}")
            
            # Collect enhanced signals
            digest_data = self._collect_telegram_digest_data()
            
            if not digest_data:
                logger.info("No signals to send in Telegram digest")
                return False
            
            # Format and send Telegram message
            message = self._format_telegram_message(digest_data)
            success = self._send_telegram_digest(message)
            
            if success:
                logger.info(f"Telegram digest sent successfully: {len(digest_data)} signals")
            else:
                logger.error("Failed to send Telegram digest")
            
            return success
            
        except Exception as e:
            logger.error(f"Error running Telegram digest: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _collect_telegram_digest_data(self) -> List[Dict]:
        """Collect enhanced signals for Telegram digest"""
        digest_data = []
        
        with SessionLocal() as db:
            for symbol in self.symbols:
                # Check if market is open for this symbol
                if not is_market_open(symbol['exchange']):
                    continue
                
                # Get latest enhanced signals for this symbol
                signals = self._get_latest_enhanced_signals(db, symbol)
                
                if signals:
                    # Analyze multi-timeframe signals
                    analysis = self._analyze_multi_timeframe_signals(signals, symbol)
                    
                    if analysis['has_signals']:
                        digest_data.append(analysis)
        
        # Sort by signal strength and confidence
        digest_data.sort(key=lambda x: (x['signal_strength'], x['confidence']), reverse=True)
        
        return digest_data[:20]  # Top 20 signals for Telegram
    
    def _get_latest_enhanced_signals(self, db, symbol: Dict) -> List[Dict]:
        """Get latest enhanced signals for a symbol"""
        try:
            # Get latest signals from all timeframes
            query = """
            SELECT s.timeframe, s.signal_type, s.confidence, s.signal_strength, s.risk_level,
                   s.stop_loss, s.take_profit, s.rr_ratio, s.analysis_notes, s.created_at
            FROM sma_signals s
            WHERE s.symbol_id = %s 
            AND s.timeframe IN %s
            AND s.created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
            ORDER BY s.created_at DESC
            """
            
            result = db.execute(query, (symbol['id'], tuple(self.timeframes)))
            signals = []
            
            for row in result:
                signals.append({
                    'timeframe': row[0],
                    'signal_type': row[1],
                    'confidence': row[2] or 0,
                    'signal_strength': row[3] or 0,
                    'risk_level': row[4] or 'medium',
                    'stop_loss': row[5],
                    'take_profit': row[6],
                    'rr_ratio': row[7],
                    'analysis_notes': row[8],
                    'created_at': row[9]
                })
            
            return signals
            
        except Exception as e:
            logger.error(f"Error getting signals for {symbol['ticker']}: {e}")
            return []
    
    def _analyze_multi_timeframe_signals(self, signals: List[Dict], symbol: Dict) -> Dict:
        """Analyze multi-timeframe signals and provide reasoning"""
        if not signals:
            return {'has_signals': False}
        
        # Group signals by type
        bullish_signals = [s for s in signals if 'bullish' in s['signal_type']]
        bearish_signals = [s for s in signals if 'bearish' in s['signal_type']]
        confirmed_signals = [s for s in signals if 'confirmed' in s['signal_type']]
        
        # Calculate overall signal strength
        total_confidence = sum(s['confidence'] for s in signals)
        avg_confidence = total_confidence / len(signals) if signals else 0
        
        # Determine primary signal
        if len(confirmed_signals) >= 2:
            primary_signal = 'CONFIRMED'
            signal_type = 'confirmed_bullish' if len([s for s in confirmed_signals if 'bullish' in s['signal_type']]) > len([s for s in confirmed_signals if 'bearish' in s['signal_type']]) else 'confirmed_bearish'
        elif len(bullish_signals) > len(bearish_signals):
            primary_signal = 'BULLISH'
            signal_type = 'local_bullish'
        elif len(bearish_signals) > len(bullish_signals):
            primary_signal = 'BEARISH'
            signal_type = 'local_bearish'
        else:
            primary_signal = 'NEUTRAL'
            signal_type = 'neutral'
        
        # Generate analysis reasoning
        reasoning = self._generate_analysis_reasoning(signals, primary_signal, symbol)
        
        # Get best risk metrics from confirmed signals
        best_signal = max(confirmed_signals, key=lambda x: x['confidence']) if confirmed_signals else signals[0]
        
        return {
            'has_signals': True,
            'symbol': symbol['ticker'],
            'company_name': symbol['company_name'],
            'exchange': symbol['exchange'],
            'primary_signal': primary_signal,
            'signal_type': signal_type,
            'confidence': avg_confidence,
            'signal_strength': len(confirmed_signals),
            'risk_level': best_signal['risk_level'],
            'stop_loss': best_signal['stop_loss'],
            'take_profit': best_signal['take_profit'],
            'rr_ratio': best_signal['rr_ratio'],
            'reasoning': reasoning,
            'timeframe_count': len(signals),
            'confirmed_count': len(confirmed_signals)
        }
    
    def _generate_analysis_reasoning(self, signals: List[Dict], primary_signal: str, symbol: Dict) -> str:
        """Generate detailed reasoning for the signal"""
        reasoning_parts = []
        
        # Timeframe analysis
        timeframes = [s['timeframe'] for s in signals]
        confirmed_tf = [s['timeframe'] for s in signals if 'confirmed' in s['signal_type']]
        
        if confirmed_tf:
            reasoning_parts.append(f"✅ Confirmed signals: {', '.join(confirmed_tf)}")
        
        # Signal strength analysis
        if primary_signal == 'CONFIRMED':
            reasoning_parts.append("🎯 Multi-timeframe confirmation - High reliability")
        elif primary_signal in ['BULLISH', 'BEARISH']:
            reasoning_parts.append("📊 Trend alignment across timeframes")
        
        # Risk assessment
        high_risk = [s for s in signals if s['risk_level'] == 'high']
        if high_risk:
            reasoning_parts.append("⚠️ High volatility detected - Use smaller position size")
        
        # Volume and momentum
        avg_confidence = sum(s['confidence'] for s in signals) / len(signals)
        if avg_confidence > 0.8:
            reasoning_parts.append("💪 Strong momentum and volume confirmation")
        elif avg_confidence > 0.6:
            reasoning_parts.append("📈 Moderate momentum - Monitor closely")
        
        return " | ".join(reasoning_parts) if reasoning_parts else "Standard SMA analysis"
    
    def _format_telegram_message(self, digest_data: List[Dict]) -> str:
        """Format Telegram message with digest data"""
        if not digest_data:
            return "📊 No active signals at this time"
        
        # Header
        timestamp = datetime.now(timezone.utc).strftime('%H:%M UTC %d/%m')
        message = f"📊 *SMA Trading Digest* - {timestamp}\n"
        message += f"🎯 {len(digest_data)} Active Signals\n\n"
        
        # Market status
        vn_open = any(d['exchange'] == 'HOSE' for d in digest_data)
        us_open = any(d['exchange'] in ['NASDAQ', 'NYSE'] for d in digest_data)
        
        if vn_open and us_open:
            message += "🌏 Markets: VN ✅ | US ✅\n\n"
        elif vn_open:
            message += "🇻🇳 Market: VN ✅\n\n"
        elif us_open:
            message += "🇺🇸 Market: US ✅\n\n"
        
        # Signals table
        message += "📈 *TOP SIGNALS:*\n"
        message += "```\n"
        message += f"{'Symbol':<6} {'Signal':<10} {'Conf':<4} {'Risk':<5} {'R/R':<5} {'Analysis'}\n"
        message += "-" * 80 + "\n"
        
        for i, data in enumerate(digest_data[:10], 1):  # Top 10 for Telegram
            symbol = data['symbol']
            signal = data['primary_signal'][:8]
            conf = f"{data['confidence']:.1f}"
            risk = data['risk_level'][:4].upper()
            rr = f"{data['rr_ratio']:.1f}" if data['rr_ratio'] else "N/A"
            
            # Truncate analysis for table
            analysis = data['reasoning'][:25] + "..." if len(data['reasoning']) > 25 else data['reasoning']
            
            message += f"{symbol:<6} {signal:<10} {conf:<4} {risk:<5} {rr:<5} {analysis}\n"
        
        message += "```\n\n"
        
        # Top 3 detailed analysis
        message += "🔍 *DETAILED ANALYSIS (Top 3):*\n\n"
        
        for i, data in enumerate(digest_data[:3], 1):
            message += f"*{i}. {data['symbol']} ({data['company_name']})*\n"
            message += f"🎯 Signal: {data['primary_signal']}\n"
            message += f"📊 Confidence: {data['confidence']:.1f}/10\n"
            message += f"⚠️ Risk: {data['risk_level'].upper()}\n"
            
            if data['stop_loss'] and data['take_profit']:
                message += f"🛡️ SL: {data['stop_loss']:.2f} | 🎯 TP: {data['take_profit']:.2f}\n"
                message += f"📈 R/R: {data['rr_ratio']:.1f}\n"
            
            message += f"💡 Analysis: {data['reasoning']}\n\n"
        
        # Footer
        message += "📱 *Trading Guidelines:*\n"
        message += "• Use proper position sizing\n"
        message += "• Set stop losses as indicated\n"
        message += "• Monitor market conditions\n"
        message += "• Risk management is key\n\n"
        message += "🔄 Next update in 5 minutes"
        
        return message
    
    def _send_telegram_digest(self, message: str) -> bool:
        """Send Telegram digest message"""
        if not self.telegram_service.is_configured():
            logger.warning("Telegram not configured, skipping digest")
            return False
        
        try:
            # Send message using existing telegram service
            success = self.telegram_service._send_telegram_message(message)
            return success
            
        except Exception as e:
            logger.error(f"Error sending Telegram digest: {e}")
            return False
    
    def run_loop(self):
        """Run Telegram digest in a loop"""
        logger.info(f"Starting Telegram digest loop; interval={self.interval} seconds")
        
        while True:
            try:
                self.run_telegram_digest()
                time.sleep(self.interval)
                
            except KeyboardInterrupt:
                logger.info("Telegram digest loop stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in Telegram digest loop: {e}")
                time.sleep(60)  # Wait 1 minute before retry

def main():
    """Main function"""
    # Initialize database
    init_db(os.getenv("DATABASE_URL"))
    
    # Create and run digest
    digest = TelegramDigest()
    digest.run_loop()

if __name__ == "__main__":
    main()
