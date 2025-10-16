#!/usr/bin/env python3
"""
VN30 Realtime Monitor - Theo dõi VN30 Index realtime
Lấy dữ liệu realtime, kết hợp với lịch sử để tính MACD và SMA
Sử dụng YAML config thay vì DB thresholds
"""

import os
import sys
import asyncio
import logging
import yaml
import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
import pytz
from typing import Dict, List, Optional, Any
import requests
import json

# Telegram service
from app.services.sma_telegram_service import SMATelegramService

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/vn30_realtime.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# VN30 Index configuration
VN30_CONFIG = {
    'symbol': 'VN30',
    'exchange': 'HOSE',
    'symbol_id': 1,  # VN30 Index ID in database
    'timeframes': ['1m', '2m', '5m'],
    'market_hours': {
        'timezone': 'Asia/Ho_Chi_Minh',
        'morning_open': time(9, 0),
        'morning_close': time(11, 30),
        'afternoon_open': time(13, 0),
        'afternoon_close': time(15, 0),
        'weekdays': [0, 1, 2, 3, 4]  # Monday to Friday
    }
}

class VN30RealtimeMonitor:
    """VN30 Realtime Monitor với YAML config"""
    
    def __init__(self):
        self.config = self._load_yaml_config()
        self.session_local = None
        self.last_processed_timestamps = {tf: None for tf in VN30_CONFIG['timeframes']}
        self._init_database()
        # Telegram
        self.telegram_service = SMATelegramService()
        self._last_sent: Dict[str, Dict[str, Any]] = {tf: {'sig': None, 'ts': None} for tf in VN30_CONFIG['timeframes']}
        
    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load configuration from YAML files"""
        try:
            # Load VN30 specific config
            vn30_config_path = 'config/symbols/VN30.yaml'
            if os.path.exists(vn30_config_path):
                with open(vn30_config_path, 'r', encoding='utf-8') as f:
                    vn30_config = yaml.safe_load(f)
            else:
                # Default VN30 config
                vn30_config = {
                    'macd': {
                        'fmacd': {
                            'igr': 0.8, 'greed': 0.5, 'bull': 0.2, 'pos': 0.1,
                            'neutral': [-0.1, 0.1], 'neg': -0.1, 'bear': -0.2, 'fear': -0.5, 'panic': -0.8
                        },
                        'smacd': {
                            'igr': 0.8, 'greed': 0.5, 'bull': 0.2, 'pos': 0.1,
                            'neutral': [-0.1, 0.1], 'neg': -0.1, 'bear': -0.2, 'fear': -0.5, 'panic': -0.8
                        },
                        'bars': {
                            'igr': 0.8, 'greed': 0.5, 'bull': 0.2, 'pos': 0.1,
                            'neutral': [-0.1, 0.1], 'neg': -0.1, 'bear': -0.2, 'fear': -0.5, 'panic': -0.8
                        }
                    },
                    'sma': {
                        'm1_period': 18,
                        'm2_period': 36,
                        'm3_period': 48,
                        'ma144_period': 144
                    }
                }
            
            # Load market config
            market_config_path = 'config/vn_market.yaml'
            if os.path.exists(market_config_path):
                with open(market_config_path, 'r', encoding='utf-8') as f:
                    market_config = yaml.safe_load(f)
            else:
                market_config = {}
            
            return {
                'vn30': vn30_config,
                'market': market_config
            }
            
        except Exception as e:
            logger.error(f"Error loading YAML config: {e}")
            return {}
    
    def _init_database(self):
        """Initialize database connection"""
        try:
            from app.db import init_db
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                init_db(database_url)
                # Import SessionLocal after init_db
                from app.db import SessionLocal
                self.session_local = SessionLocal
                logger.info("✅ Database initialized for VN30 Realtime Monitor")
            else:
                logger.error("DATABASE_URL environment variable not set")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def is_market_open(self) -> bool:
        """Check if VN market is open"""
        try:
            market_config = VN30_CONFIG['market_hours']
            tz = pytz.timezone(market_config['timezone'])
            now = datetime.now(tz)
            current_time = now.time()
            current_weekday = now.weekday()
            
            # Check if it's a weekday
            if current_weekday not in market_config['weekdays']:
                return False
            
            # Check if within market hours (excluding lunch break)
            morning_open = market_config['morning_open']
            morning_close = market_config['morning_close']
            afternoon_open = market_config['afternoon_open']
            afternoon_close = market_config['afternoon_close']
            
            return ((morning_open <= current_time <= morning_close) or 
                   (afternoon_open <= current_time <= afternoon_close))
            
        except Exception as e:
            logger.error(f"Error checking market status: {e}")
            return False
    
    def get_realtime_data(self) -> Optional[Dict[str, Any]]:
        """Get realtime VN30 data from API"""
        try:
            # This is a placeholder - you would implement actual API call here
            # For now, we'll simulate realtime data
            current_price = 1800 + np.random.normal(0, 10)  # Simulate price around 1800
            
            return {
                'symbol': VN30_CONFIG['symbol'],
                'price': current_price,
                'timestamp': datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')),
                'volume': np.random.randint(1000, 5000)
            }
            
        except Exception as e:
            logger.error(f"Error getting realtime data: {e}")
            return None
    
    def get_historical_data(self, timeframe: str, limit: int = 200) -> Optional[pd.DataFrame]:
        """Get historical data from database"""
        try:
            with self.session_local() as s:
                from sqlalchemy import text
                
                query = text("""
                    SELECT ts, open, high, low, close, volume
                    FROM candles_tf
                    WHERE symbol_id = :symbol_id AND timeframe = :timeframe
                    ORDER BY ts DESC
                    LIMIT :limit
                """)
                
                result = s.execute(query, {
                    'symbol_id': VN30_CONFIG['symbol_id'],
                    'timeframe': timeframe,
                    'limit': limit
                })
                
                data = []
                for row in result:
                    data.append({
                        'timestamp': row.ts,
                        'open': float(row.open),
                        'high': float(row.high),
                        'low': float(row.low),
                        'close': float(row.close),
                        'volume': float(row.volume)
                    })
                
                if data:
                    df = pd.DataFrame(data)
                    df = df.sort_values('timestamp').reset_index(drop=True)
                    return df
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting historical data for {timeframe}: {e}")
            return None
    
    def calculate_sma_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate SMA indicators"""
        try:
            config = self.config['vn30']['sma']
            
            # Calculate moving averages
            m1 = df['close'].rolling(window=config['m1_period']).mean().iloc[-1]
            m2 = df['close'].rolling(window=config['m2_period']).mean().iloc[-1]
            m3 = df['close'].rolling(window=config['m3_period']).mean().iloc[-1]
            ma144 = df['close'].rolling(window=config['ma144_period']).mean().iloc[-1]
            
            # Calculate average of m1, m2, m3
            avg_m1_m2_m3 = (m1 + m2 + m3) / 3
            
            return {
                'close': float(df['close'].iloc[-1]),
                'm1': float(m1),
                'm2': float(m2),
                'm3': float(m3),
                'ma144': float(ma144),
                'avg_m1_m2_m3': float(avg_m1_m2_m3)
            }
            
        except Exception as e:
            logger.error(f"Error calculating SMA indicators: {e}")
            return {}
    
    def calculate_macd_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate MACD indicators"""
        try:
            # Calculate MACD (12, 26, 9)
            exp1 = df['close'].ewm(span=12).mean()
            exp2 = df['close'].ewm(span=26).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9).mean()
            histogram = macd - signal
            
            return {
                'macd': float(macd.iloc[-1]),
                'macd_signal': float(signal.iloc[-1]),
                'histogram': float(histogram.iloc[-1])
            }
            
        except Exception as e:
            logger.error(f"Error calculating MACD indicators: {e}")
            return {}
    
    def evaluate_sma_signal(self, sma_data: Dict[str, float]) -> Dict[str, Any]:
        """Evaluate SMA signal using YAML config"""
        try:
            close = sma_data['close']
            m1 = sma_data['m1']
            m2 = sma_data['m2']
            m3 = sma_data['m3']
            ma144 = sma_data['ma144']
            avg_m1_m2_m3 = sma_data['avg_m1_m2_m3']
            
            # SMA Signal Logic
            if close > m1 > m2 > m3 > ma144:
                signal_type = 'STRONG_BUY'
                direction = 'BUY'
                strength = 0.9
            elif close > m1 > m2 and m3 > ma144:
                signal_type = 'BUY'
                direction = 'BUY'
                strength = 0.7
            elif close > avg_m1_m2_m3:
                signal_type = 'WEAK_BUY'
                direction = 'BUY'
                strength = 0.5
            elif close < m1 < m2 < m3 < ma144:
                signal_type = 'STRONG_SELL'
                direction = 'SELL'
                strength = 0.9
            elif close < m1 < m2 and m3 < ma144:
                signal_type = 'SELL'
                direction = 'SELL'
                strength = 0.7
            elif close < avg_m1_m2_m3:
                signal_type = 'WEAK_SELL'
                direction = 'SELL'
                strength = 0.5
            else:
                signal_type = 'NEUTRAL'
                direction = 'NEUTRAL'
                strength = 0.3
            
            return {
                'signal_type': signal_type,
                'direction': direction,
                'strength': strength,
                'details': sma_data
            }
            
        except Exception as e:
            logger.error(f"Error evaluating SMA signal: {e}")
            return {'signal_type': 'NEUTRAL', 'direction': 'NEUTRAL', 'strength': 0.0}
    
    def evaluate_macd_signal(self, macd_data: Dict[str, float]) -> Dict[str, Any]:
        """Evaluate MACD signal using YAML config"""
        try:
            config = self.config['vn30']['macd']
            macd = macd_data['macd']
            macd_signal = macd_data['macd_signal']
            histogram = macd_data['histogram']
            
            # Get thresholds from config
            fmacd_thresholds = config['fmacd']
            smacd_thresholds = config['smacd']
            bars_thresholds = config['bars']
            
            # Evaluate FMACD zone
            if macd >= fmacd_thresholds['igr']:
                f_zone = 'igr'
            elif macd >= fmacd_thresholds['greed']:
                f_zone = 'greed'
            elif macd >= fmacd_thresholds['bull']:
                f_zone = 'bull'
            elif macd >= fmacd_thresholds['pos']:
                f_zone = 'pos'
            elif fmacd_thresholds['neutral'][0] <= macd <= fmacd_thresholds['neutral'][1]:
                f_zone = 'neutral'
            elif macd <= fmacd_thresholds['neg']:
                f_zone = 'neg'
            elif macd <= fmacd_thresholds['bear']:
                f_zone = 'bear'
            elif macd <= fmacd_thresholds['fear']:
                f_zone = 'fear'
            else:
                f_zone = 'panic'
            
            # Evaluate SMACD zone
            if macd_signal >= smacd_thresholds['igr']:
                s_zone = 'igr'
            elif macd_signal >= smacd_thresholds['greed']:
                s_zone = 'greed'
            elif macd_signal >= smacd_thresholds['bull']:
                s_zone = 'bull'
            elif macd_signal >= smacd_thresholds['pos']:
                s_zone = 'pos'
            elif smacd_thresholds['neutral'][0] <= macd_signal <= smacd_thresholds['neutral'][1]:
                s_zone = 'neutral'
            elif macd_signal <= smacd_thresholds['neg']:
                s_zone = 'neg'
            elif macd_signal <= smacd_thresholds['bear']:
                s_zone = 'bear'
            elif macd_signal <= smacd_thresholds['fear']:
                s_zone = 'fear'
            else:
                s_zone = 'panic'
            
            # Evaluate Bars zone
            bars_abs = abs(histogram)
            if bars_abs >= bars_thresholds['igr']:
                bars_zone = 'igr'
            elif bars_abs >= bars_thresholds['greed']:
                bars_zone = 'greed'
            elif bars_abs >= bars_thresholds['bull']:
                bars_zone = 'bull'
            elif bars_abs >= bars_thresholds['pos']:
                bars_zone = 'pos'
            elif bars_thresholds['neutral'][0] <= bars_abs <= bars_thresholds['neutral'][1]:
                bars_zone = 'neutral'
            elif bars_abs <= bars_thresholds['neg']:
                bars_zone = 'neg'
            elif bars_abs <= bars_thresholds['bear']:
                bars_zone = 'bear'
            elif bars_abs <= bars_thresholds['fear']:
                bars_zone = 'fear'
            else:
                bars_zone = 'panic'
            
            # Determine signal based on zones
            if f_zone in ['igr', 'greed', 'bull'] and s_zone in ['igr', 'greed', 'bull']:
                signal_type = 'STRONG_BUY'
                direction = 'BUY'
                strength = 0.9
            elif f_zone in ['igr', 'greed', 'bull'] or s_zone in ['igr', 'greed', 'bull']:
                signal_type = 'BUY'
                direction = 'BUY'
                strength = 0.7
            elif f_zone in ['panic', 'fear', 'bear'] and s_zone in ['panic', 'fear', 'bear']:
                signal_type = 'STRONG_SELL'
                direction = 'SELL'
                strength = 0.9
            elif f_zone in ['panic', 'fear', 'bear'] or s_zone in ['panic', 'fear', 'bear']:
                signal_type = 'SELL'
                direction = 'SELL'
                strength = 0.7
            else:
                signal_type = 'NEUTRAL'
                direction = 'NEUTRAL'
                strength = 0.3
            
            return {
                'signal_type': signal_type,
                'direction': direction,
                'strength': strength,
                'details': {
                    'macd': macd,
                    'macd_signal': macd_signal,
                    'histogram': histogram,
                    'f_zone': f_zone,
                    's_zone': s_zone,
                    'bars_zone': bars_zone
                }
            }
            
        except Exception as e:
            logger.error(f"Error evaluating MACD signal: {e}")
            return {'signal_type': 'NEUTRAL', 'direction': 'NEUTRAL', 'strength': 0.0}
    
    def combine_signals(self, sma_signal: Dict, macd_signal: Dict) -> Dict[str, Any]:
        """Combine SMA and MACD signals"""
        try:
            sma_direction = sma_signal.get('direction', 'NEUTRAL')
            macd_direction = macd_signal.get('direction', 'NEUTRAL')
            sma_strength = sma_signal.get('strength', 0.0)
            macd_strength = macd_signal.get('strength', 0.0)
            
            # Combination logic
            if sma_direction == 'BUY' and macd_direction == 'BUY':
                signal_type = 'STRONG_BUY'
                direction = 'BUY'
                strength = min(sma_strength + macd_strength, 1.0)
                logic = "Both SMA and MACD bullish"
            elif sma_direction == 'SELL' and macd_direction == 'SELL':
                signal_type = 'STRONG_SELL'
                direction = 'SELL'
                strength = min(sma_strength + macd_strength, 1.0)
                logic = "Both SMA and MACD bearish"
            elif sma_direction == 'BUY' and macd_direction == 'NEUTRAL':
                signal_type = 'BUY'
                direction = 'BUY'
                strength = sma_strength * 0.7
                logic = "SMA bullish, MACD neutral"
            elif sma_direction == 'NEUTRAL' and macd_direction == 'BUY':
                signal_type = 'BUY'
                direction = 'BUY'
                strength = macd_strength * 0.7
                logic = "MACD bullish, SMA neutral"
            elif sma_direction == 'SELL' and macd_direction == 'NEUTRAL':
                signal_type = 'SELL'
                direction = 'SELL'
                strength = sma_strength * 0.7
                logic = "SMA bearish, MACD neutral"
            elif sma_direction == 'NEUTRAL' and macd_direction == 'SELL':
                signal_type = 'SELL'
                direction = 'SELL'
                strength = macd_strength * 0.7
                logic = "MACD bearish, SMA neutral"
            elif sma_direction == 'BUY' and macd_direction == 'SELL':
                signal_type = 'WEAK_BUY'
                direction = 'BUY'
                strength = abs(sma_strength - macd_strength) * 0.3
                logic = "SMA bullish, MACD bearish (conflict)"
            elif sma_direction == 'SELL' and macd_direction == 'BUY':
                signal_type = 'WEAK_SELL'
                direction = 'SELL'
                strength = abs(sma_strength - macd_strength) * 0.3
                logic = "SMA bearish, MACD bullish (conflict)"
            else:
                signal_type = 'NEUTRAL'
                direction = 'NEUTRAL'
                strength = 0.0
                logic = "Both SMA and MACD neutral"
            
            # Calculate confidence
            confidence = (sma_strength + macd_strength) / 2
            
            return {
                'signal_type': signal_type,
                'direction': direction,
                'strength': strength,
                'confidence': confidence,
                'logic': logic,
                'sma_signal': sma_signal,
                'macd_signal': macd_signal
            }
            
        except Exception as e:
            logger.error(f"Error combining signals: {e}")
            return {'signal_type': 'NEUTRAL', 'direction': 'NEUTRAL', 'strength': 0.0, 'confidence': 0.0}
    
    async def process_timeframe(self, timeframe: str) -> Optional[Dict[str, Any]]:
        """Process a single timeframe"""
        try:
            logger.info(f"🔄 Processing {timeframe} timeframe...")
            
            # Get historical data
            historical_df = self.get_historical_data(timeframe, limit=200)
            if historical_df is None:
                logger.warning(f"No historical data available for {timeframe}")
                return None
            if len(historical_df) < 50:
                logger.warning(f"Insufficient historical data for {timeframe}: {len(historical_df)} candles (need at least 50)")
                return None
            
            # Get realtime data
            realtime_data = self.get_realtime_data()
            if realtime_data is None:
                logger.warning(f"No realtime data available for {timeframe}")
                return None
            
            # Add realtime data to historical data
            # Convert realtime timestamp to timezone-naive for consistency
            realtime_timestamp = realtime_data['timestamp']
            if realtime_timestamp.tzinfo is not None:
                realtime_timestamp = realtime_timestamp.replace(tzinfo=None)
            
            new_row = pd.DataFrame([{
                'timestamp': realtime_timestamp,
                'open': realtime_data['price'],
                'high': realtime_data['price'],
                'low': realtime_data['price'],
                'close': realtime_data['price'],
                'volume': realtime_data['volume']
            }])
            
            # Combine data
            combined_df = pd.concat([historical_df, new_row], ignore_index=True)
            combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)
            
            # Calculate indicators
            sma_data = self.calculate_sma_indicators(combined_df)
            macd_data = self.calculate_macd_indicators(combined_df)
            
            if not sma_data or not macd_data:
                logger.warning(f"Failed to calculate indicators for {timeframe}")
                return None
            
            # Evaluate signals
            sma_signal = self.evaluate_sma_signal(sma_data)
            macd_signal = self.evaluate_macd_signal(macd_data)
            
            # Combine signals
            hybrid_signal = self.combine_signals(sma_signal, macd_signal)
            
            result = {
                'timeframe': timeframe,
                'timestamp': realtime_data['timestamp'].isoformat(),
                'price': realtime_data['price'],
                'hybrid_signal': hybrid_signal,
                'sma_data': sma_data,
                'macd_data': macd_data
            }
            
            logger.info(f"✅ {timeframe} processed: {hybrid_signal['signal_type']} ({hybrid_signal['direction']}) - Confidence: {hybrid_signal['confidence']:.2f}")

            # Send Telegram (de-dup simple by signal_type + direction change)
            try:
                if self.telegram_service.is_configured():
                    sig_key = f"{hybrid_signal['signal_type']}_{hybrid_signal['direction']}"
                    last = self._last_sent.get(timeframe, {})
                    if last.get('sig') != sig_key:
                        # build concise message using SMA details and overall hybrid result
                        msg_signal = {
                            'signal_type': hybrid_signal['signal_type'],
                            'signal_direction': hybrid_signal['direction'],
                            'signal_strength': hybrid_signal['strength'],
                            **sma_signal.get('details', {})
                        }
                        self.telegram_service._send_telegram_message(
                            f"📣 VN30 {timeframe} → {hybrid_signal['signal_type']} ({hybrid_signal['direction']})\n"
                            f"🎯 Confidence: {hybrid_signal['confidence']:.2f}\n"
                            f"💰 Price: {result['price']:.2f}"
                        )
                        self._last_sent[timeframe] = {'sig': sig_key, 'ts': datetime.utcnow()}
                else:
                    logger.debug("Telegram not configured; skipping message")
            except Exception as e:
                logger.error(f"Telegram send error: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing {timeframe}: {e}")
            return None
    
    async def run_cycle(self):
        """Run a single monitoring cycle"""
        try:
            logger.info("🔄 VN30 Realtime Cycle Started")
            
            results = []
            for timeframe in VN30_CONFIG['timeframes']:
                result = await self.process_timeframe(timeframe)
                if result:
                    results.append(result)
            
            if results:
                # Aggregate results
                signals = [r['hybrid_signal']['signal_type'] for r in results]
                directions = [r['hybrid_signal']['direction'] for r in results]
                confidences = [r['hybrid_signal']['confidence'] for r in results]
                
                # Calculate overall signal
                overall_confidence = sum(confidences) / len(confidences)
                
                # Majority vote for direction
                direction_counts = {}
                for direction in directions:
                    direction_counts[direction] = direction_counts.get(direction, 0) + 1
                overall_direction = max(direction_counts, key=direction_counts.get)
                
                # Determine overall signal
                if overall_confidence > 0.7:
                    if overall_direction == 'BUY':
                        overall_signal = 'STRONG_BUY'
                    elif overall_direction == 'SELL':
                        overall_signal = 'STRONG_SELL'
                    else:
                        overall_signal = 'NEUTRAL'
                elif overall_confidence > 0.5:
                    if overall_direction == 'BUY':
                        overall_signal = 'BUY'
                    elif overall_direction == 'SELL':
                        overall_signal = 'SELL'
                    else:
                        overall_signal = 'NEUTRAL'
                else:
                    overall_signal = 'NEUTRAL'
                
                # Log results
                logger.info("\n📊 VN30 REALTIME SUMMARY:")
                for result in results:
                    tf = result['timeframe']
                    signal = result['hybrid_signal']
                    logger.info(f"   📈 {tf}: {signal['signal_type']} ({signal['direction']}) - Confidence: {signal['confidence']:.2f}")
                
                logger.info(f"   📊 Overall: {overall_signal} ({overall_direction}) - Confidence: {overall_confidence:.2f}")
                
                # Signal strength analysis
                if overall_confidence > 0.7:
                    logger.info(f"🚨 STRONG SIGNAL: VN30 - {overall_signal} (Confidence: {overall_confidence:.2f})")
                elif overall_confidence > 0.5:
                    logger.info(f"📊 MODERATE SIGNAL: VN30 - {overall_signal} (Confidence: {overall_confidence:.2f})")
                else:
                    logger.info(f"➡️ WEAK SIGNAL: VN30 - {overall_signal} (Confidence: {overall_confidence:.2f})")
                
                # Market sentiment
                if 'BUY' in overall_signal:
                    logger.info("📈 VN30: BULLISH MARKET SENTIMENT")
                elif 'SELL' in overall_signal:
                    logger.info("📉 VN30: BEARISH MARKET SENTIMENT")
                else:
                    logger.info("➡️ VN30: NEUTRAL MARKET SENTIMENT")
                
                return {
                    'overall_signal': overall_signal,
                    'overall_direction': overall_direction,
                    'overall_confidence': overall_confidence,
                    'timeframe_results': results
                }
            else:
                logger.warning("No results generated in this cycle")
                return None
                
        except Exception as e:
            logger.error(f"Error in run_cycle: {e}")
            return None
    
    async def run(self):
        """Main monitoring loop"""
        logger.info("🚀 VN30 Realtime Monitor Started")
        logger.info(f"📊 Monitoring: {VN30_CONFIG['symbol']} - {VN30_CONFIG['exchange']}")
        logger.info(f"⏰ Timeframes: {', '.join(VN30_CONFIG['timeframes'])}")
        logger.info(f"🔄 Cycle Interval: 30 seconds")
        logger.info(f"📅 VN Market Hours: {VN30_CONFIG['market_hours']['morning_open'].strftime('%H:%M')} - {VN30_CONFIG['market_hours']['afternoon_close'].strftime('%H:%M')} (UTC+7)")
        
        while True:
            try:
                if self.is_market_open():
                    logger.info(f"✅ Market is OPEN. Current VN Time: {datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%H:%M:%S')}")
                    await self.run_cycle()
                else:
                    now_vn = datetime.now(pytz.timezone('Asia/Ho_Chi_Minh'))
                    current_time = now_vn.time()
                    weekday = now_vn.weekday()
                    
                    if not (0 <= weekday <= 4):
                        logger.info(f"😴 Market is CLOSED (Weekend). Current VN Time: {now_vn.strftime('%Y-%m-%d %H:%M:%S')}")
                    elif VN30_CONFIG['market_hours']['morning_close'] <= current_time <= VN30_CONFIG['market_hours']['afternoon_open']:
                        logger.info(f"☕ Market is on LUNCH BREAK. Current VN Time: {now_vn.strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        logger.info(f"🌙 Market is CLOSED. Current VN Time: {now_vn.strftime('%Y-%m-%d %H:%M:%S')}")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                logger.info("🛑 Received interrupt signal")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    monitor = VN30RealtimeMonitor()
    asyncio.run(monitor.run())
