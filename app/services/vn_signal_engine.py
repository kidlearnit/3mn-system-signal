#!/usr/bin/env python3
"""
VN Signal Engine - Tính tín hiệu hybrid (SMA + MACD) dùng YAML config + DB candles
Dùng cho worker_vn và vn30_monitor
"""

import os
import yaml
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from app.db import SessionLocal
from sqlalchemy import text

logger = logging.getLogger(__name__)

class VNSignalEngine:
    """Engine tính tín hiệu hybrid cho VN market dùng YAML config"""
    
    def __init__(self):
        self.config = self._load_yaml_config()
        self.session_local = SessionLocal
    
    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load config từ YAML files"""
        try:
            vn_config = {}
            
            # Load VN-specific config
            vn_config_path = 'config/symbols/VN30.yaml'
            if os.path.exists(vn_config_path):
                with open(vn_config_path, 'r', encoding='utf-8') as f:
                    vn_config = yaml.safe_load(f) or {}
            else:
                # Default config nếu không có file
                vn_config = {
                    'macd': {
                        'fmacd': {'igr': 0.8, 'greed': 0.5, 'bull': 0.2, 'pos': 0.1, 'neutral': [-0.1, 0.1], 'neg': -0.1, 'bear': -0.2, 'fear': -0.5, 'panic': -0.8},
                        'smacd': {'igr': 0.8, 'greed': 0.5, 'bull': 0.2, 'pos': 0.1, 'neutral': [-0.1, 0.1], 'neg': -0.1, 'bear': -0.2, 'fear': -0.5, 'panic': -0.8},
                        'bars': {'igr': 0.8, 'greed': 0.5, 'bull': 0.2, 'pos': 0.1, 'neutral': [-0.1, 0.1], 'neg': -0.1, 'bear': -0.2, 'fear': -0.5, 'panic': -0.8}
                    },
                    'sma': {'m1_period': 18, 'm2_period': 36, 'm3_period': 48, 'ma144_period': 144}
                }
            
            return {'vn': vn_config}
        except Exception as e:
            logger.error(f"Error loading YAML config: {e}")
            return {}
    
    def get_historical_data(self, symbol_id: int, timeframe: str, limit: int = 200) -> Optional[pd.DataFrame]:
        """Lấy dữ liệu lịch sử từ DB - try candles_tf first, then fallback to candles_1m with resampling"""
        try:
            with self.session_local() as s:
                # Try candles_tf first
                query = text("""
                    SELECT ts, open, high, low, close, volume
                    FROM candles_tf
                    WHERE symbol_id = :symbol_id AND timeframe = :timeframe
                    ORDER BY ts DESC
                    LIMIT :limit
                """)
                
                result = s.execute(query, {
                    'symbol_id': symbol_id,
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
                
                # If candles_tf has data, use it
                if data:
                    df = pd.DataFrame(data)
                    df = df.sort_values('timestamp').reset_index(drop=True)
                    return df
                
                # Otherwise, fallback to candles_1m and resample
                logger.info(f"candles_tf empty for {symbol_id} {timeframe}, falling back to candles_1m")
                
                # Get 1m candles and resample
                limit_1m = limit * int(timeframe.replace('m', '')) if 'm' in timeframe else limit * 60
                query_1m = text("""
                    SELECT ts, open, high, low, close, volume
                    FROM candles_1m
                    WHERE symbol_id = :symbol_id
                    ORDER BY ts DESC
                    LIMIT :limit
                """)
                
                result_1m = s.execute(query_1m, {
                    'symbol_id': symbol_id,
                    'limit': limit_1m
                })
                
                data_1m = []
                for row in result_1m:
                    data_1m.append({
                        'timestamp': row.ts,
                        'open': float(row.open),
                        'high': float(row.high),
                        'low': float(row.low),
                        'close': float(row.close),
                        'volume': float(row.volume)
                    })
                
                if not data_1m:
                    return None
                
                # Convert to DataFrame and resample
                df = pd.DataFrame(data_1m)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp').set_index('timestamp')
                
                # Resample to target timeframe
                tf_minutes = int(timeframe.replace('m', '')) if 'm' in timeframe else 1
                resampled = df.resample(f'{tf_minutes}min').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna()
                
                resampled = resampled.reset_index()
                resampled.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                
                if len(resampled) >= 50:
                    return resampled
                else:
                    logger.warning(f"Resampled data insufficient: {len(resampled)} candles (need 50+)")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol_id} {timeframe}: {e}")
            return None
    
    def calculate_sma(self, df: pd.DataFrame) -> Dict[str, float]:
        """Tính SMA indicators"""
        try:
            config = self.config.get('vn', {}).get('sma', {})
            m1 = df['close'].rolling(window=config.get('m1_period', 18)).mean().iloc[-1]
            m2 = df['close'].rolling(window=config.get('m2_period', 36)).mean().iloc[-1]
            m3 = df['close'].rolling(window=config.get('m3_period', 48)).mean().iloc[-1]
            ma144 = df['close'].rolling(window=config.get('ma144_period', 144)).mean().iloc[-1]
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
            logger.error(f"Error calculating SMA: {e}")
            return {}
    
    def calculate_macd(self, df: pd.DataFrame) -> Dict[str, float]:
        """Tính MACD indicators"""
        try:
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
            logger.error(f"Error calculating MACD: {e}")
            return {}
    
    def evaluate_sma_signal(self, sma_data: Dict[str, float]) -> Dict[str, Any]:
        """Đánh giá SMA signal"""
        try:
            close = sma_data['close']
            m1, m2, m3 = sma_data['m1'], sma_data['m2'], sma_data['m3']
            ma144 = sma_data['ma144']
            avg_m1_m2_m3 = sma_data['avg_m1_m2_m3']
            
            if close > m1 > m2 > m3 > ma144:
                return {'signal_type': 'STRONG_BUY', 'direction': 'BUY', 'strength': 0.9}
            elif close > m1 > m2 and m3 > ma144:
                return {'signal_type': 'BUY', 'direction': 'BUY', 'strength': 0.7}
            elif close > avg_m1_m2_m3:
                return {'signal_type': 'WEAK_BUY', 'direction': 'BUY', 'strength': 0.5}
            elif close < m1 < m2 < m3 < ma144:
                return {'signal_type': 'STRONG_SELL', 'direction': 'SELL', 'strength': 0.9}
            elif close < m1 < m2 and m3 < ma144:
                return {'signal_type': 'SELL', 'direction': 'SELL', 'strength': 0.7}
            elif close < avg_m1_m2_m3:
                return {'signal_type': 'WEAK_SELL', 'direction': 'SELL', 'strength': 0.5}
            else:
                return {'signal_type': 'NEUTRAL', 'direction': 'NEUTRAL', 'strength': 0.3}
        except Exception as e:
            logger.error(f"Error evaluating SMA signal: {e}")
            return {'signal_type': 'NEUTRAL', 'direction': 'NEUTRAL', 'strength': 0.0}
    
    def evaluate_macd_signal(self, macd_data: Dict[str, float]) -> Dict[str, Any]:
        """Đánh giá MACD signal dùng YAML thresholds"""
        try:
            config = self.config.get('vn', {}).get('macd', {})
            macd = macd_data['macd']
            macd_signal = macd_data['macd_signal']
            histogram = macd_data['histogram']
            
            fmacd_t = config.get('fmacd', {})
            smacd_t = config.get('smacd', {})
            bars_t = config.get('bars', {})
            
            # Determine zones
            def get_zone(val, thresholds):
                if val >= thresholds.get('igr', 0.8):
                    return 'igr'
                elif val >= thresholds.get('greed', 0.5):
                    return 'greed'
                elif val >= thresholds.get('bull', 0.2):
                    return 'bull'
                elif val >= thresholds.get('pos', 0.1):
                    return 'pos'
                elif isinstance(thresholds.get('neutral'), list) and thresholds['neutral'][0] <= val <= thresholds['neutral'][1]:
                    return 'neutral'
                elif val <= thresholds.get('neg', -0.1):
                    return 'neg'
                elif val <= thresholds.get('bear', -0.2):
                    return 'bear'
                elif val <= thresholds.get('fear', -0.5):
                    return 'fear'
                else:
                    return 'panic'
            
            f_zone = get_zone(macd, fmacd_t)
            s_zone = get_zone(macd_signal, smacd_t)
            bars_zone = get_zone(abs(histogram), bars_t)
            
            # Determine signal
            if f_zone in ['igr', 'greed', 'bull'] and s_zone in ['igr', 'greed', 'bull']:
                return {'signal_type': 'STRONG_BUY', 'direction': 'BUY', 'strength': 0.9}
            elif f_zone in ['igr', 'greed', 'bull'] or s_zone in ['igr', 'greed', 'bull']:
                return {'signal_type': 'BUY', 'direction': 'BUY', 'strength': 0.7}
            elif f_zone in ['panic', 'fear', 'bear'] and s_zone in ['panic', 'fear', 'bear']:
                return {'signal_type': 'STRONG_SELL', 'direction': 'SELL', 'strength': 0.9}
            elif f_zone in ['panic', 'fear', 'bear'] or s_zone in ['panic', 'fear', 'bear']:
                return {'signal_type': 'SELL', 'direction': 'SELL', 'strength': 0.7}
            else:
                return {'signal_type': 'NEUTRAL', 'direction': 'NEUTRAL', 'strength': 0.3}
        except Exception as e:
            logger.error(f"Error evaluating MACD signal: {e}")
            return {'signal_type': 'NEUTRAL', 'direction': 'NEUTRAL', 'strength': 0.0}
    
    def combine_signals(self, sma_signal: Dict, macd_signal: Dict) -> Dict[str, Any]:
        """Kết hợp SMA + MACD signals"""
        try:
            sma_dir = sma_signal.get('direction', 'NEUTRAL')
            macd_dir = macd_signal.get('direction', 'NEUTRAL')
            sma_str = sma_signal.get('strength', 0.0)
            macd_str = macd_signal.get('strength', 0.0)
            
            if sma_dir == 'BUY' and macd_dir == 'BUY':
                return {'signal': 'STRONG_BUY', 'direction': 'BUY', 'strength': min(sma_str + macd_str, 1.0), 'confidence': (sma_str + macd_str) / 2}
            elif sma_dir == 'SELL' and macd_dir == 'SELL':
                return {'signal': 'STRONG_SELL', 'direction': 'SELL', 'strength': min(sma_str + macd_str, 1.0), 'confidence': (sma_str + macd_str) / 2}
            elif (sma_dir == 'BUY' and macd_dir == 'NEUTRAL') or (sma_dir == 'NEUTRAL' and macd_dir == 'BUY'):
                return {'signal': 'BUY', 'direction': 'BUY', 'strength': max(sma_str, macd_str) * 0.7, 'confidence': (sma_str + macd_str) / 2}
            elif (sma_dir == 'SELL' and macd_dir == 'NEUTRAL') or (sma_dir == 'NEUTRAL' and macd_dir == 'SELL'):
                return {'signal': 'SELL', 'direction': 'SELL', 'strength': max(sma_str, macd_str) * 0.7, 'confidence': (sma_str + macd_str) / 2}
            elif sma_dir == 'BUY' and macd_dir == 'SELL':
                return {'signal': 'WEAK_BUY', 'direction': 'BUY', 'strength': abs(sma_str - macd_str) * 0.3, 'confidence': (sma_str + macd_str) / 2}
            elif sma_dir == 'SELL' and macd_dir == 'BUY':
                return {'signal': 'WEAK_SELL', 'direction': 'SELL', 'strength': abs(sma_str - macd_str) * 0.3, 'confidence': (sma_str + macd_str) / 2}
            else:
                return {'signal': 'NEUTRAL', 'direction': 'NEUTRAL', 'strength': 0.0, 'confidence': 0.0}
        except Exception as e:
            logger.error(f"Error combining signals: {e}")
            return {'signal': 'NEUTRAL', 'direction': 'NEUTRAL', 'strength': 0.0, 'confidence': 0.0}
    
    def evaluate(self, symbol_id: int, ticker: str, exchange: str, timeframe: str) -> Dict[str, Any]:
        """Evaluate hybrid signal for a single timeframe"""
        try:
            # Get historical data
            df = self.get_historical_data(symbol_id, timeframe, 200)
            if df is None or len(df) < 50:
                logger.warning(f"Insufficient data for {ticker} {timeframe}")
                return {'signal': 'NEUTRAL', 'direction': 'NEUTRAL', 'confidence': 0.0, 'error': 'Insufficient data'}
            
            # Calculate indicators
            sma_data = self.calculate_sma(df)
            macd_data = self.calculate_macd(df)
            
            if not sma_data or not macd_data:
                return {'signal': 'NEUTRAL', 'direction': 'NEUTRAL', 'confidence': 0.0, 'error': 'Failed to calculate indicators'}
            
            # Evaluate signals
            sma_signal = self.evaluate_sma_signal(sma_data)
            macd_signal = self.evaluate_macd_signal(macd_data)
            
            # Combine signals
            hybrid = self.combine_signals(sma_signal, macd_signal)
            
            return {
                'symbol_id': symbol_id,
                'ticker': ticker,
                'exchange': exchange,
                'timeframe': timeframe,
                'timestamp': datetime.now().isoformat(),
                **hybrid,
                'sma_data': sma_data,
                'macd_data': macd_data
            }
        except Exception as e:
            logger.error(f"Error evaluating signal for {ticker} {timeframe}: {e}")
            return {'signal': 'NEUTRAL', 'direction': 'NEUTRAL', 'confidence': 0.0, 'error': str(e)}

# Global instance
vn_signal_engine = VNSignalEngine()
