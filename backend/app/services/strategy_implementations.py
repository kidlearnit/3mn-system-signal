#!/usr/bin/env python3
"""
Strategy Implementations - Các implementation cụ thể của strategies
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy import text

from .strategy_base import BaseStrategy, StrategyConfig, SignalResult, SignalDirection
from .sma_signal_engine import sma_signal_engine
from .signal_engine import match_zone_with_thresholds, make_signal
from ..db import init_db
import logging
import os

# Initialize database
init_db(os.getenv("DATABASE_URL"))

# Import SessionLocal after initialization
from ..db import SessionLocal

logger = logging.getLogger(__name__)

class SMAStrategy(BaseStrategy):
    """SMA Strategy Implementation"""
    
    def __init__(self, config: StrategyConfig = None):
        if config is None:
            config = StrategyConfig(
                name="SMA Strategy",
                description="Simple Moving Average based strategy",
                version="1.0.0",
                weight=1.0,
                min_confidence=0.5,
                parameters={
                    'ma_periods': [18, 36, 48, 144],
                    'triple_confirmation': True
                }
            )
        super().__init__(config)
    
    def evaluate_signal(self, symbol_id: int, ticker: str, exchange: str, 
                       timeframe: str) -> SignalResult:
        """Đánh giá tín hiệu SMA"""
        try:
            logger.info(f"Evaluating SMA signal for {ticker} ({symbol_id}) on {timeframe}")
            with SessionLocal() as s:
                logger.info("Database session created")
                # Lấy dữ liệu SMA mới nhất
                row = s.execute(text("""
                    SELECT ts, close, m1, m2, m3, ma144, avg_m1_m2_m3
                    FROM indicators_sma
                    WHERE symbol_id = :symbol_id AND timeframe = :timeframe
                    ORDER BY ts DESC LIMIT 1
                """), {'symbol_id': symbol_id, 'timeframe': timeframe}).mappings().first()
                
                logger.info(f"Database query result: {row}")
                if not row:
                    return self._create_neutral_signal(symbol_id, ticker, exchange, timeframe, "No SMA data")
                
                # Tạo MA structure
                ma_structure = {
                    'cp': float(row['close']),
                    'm1': float(row['m1']),
                    'm2': float(row['m2']),
                    'm3': float(row['m3']),
                    'ma144': float(row['ma144']),
                    'avg_m1_m2_m3': float(row['avg_m1_m2_m3'])
                }
                logger.info(f"MA structure created: {ma_structure}")
                
                # Đánh giá tín hiệu SMA
                logger.info("Calling sma_signal_engine.evaluate_single_timeframe")
                signal_type = sma_signal_engine.evaluate_single_timeframe(ma_structure)
                logger.info(f"Signal type: {signal_type}")
                
                logger.info("Calling sma_signal_engine.get_signal_direction")
                direction = sma_signal_engine.get_signal_direction(signal_type)
                logger.info(f"Direction: {direction}")
                
                logger.info("Calling sma_signal_engine.get_signal_strength")
                strength = sma_signal_engine.get_signal_strength(signal_type)
                logger.info(f"Strength: {strength}")
                
                # Tính confidence dựa trên strength và MA alignment
                logger.info("Calculating confidence")
                confidence = self._calculate_sma_confidence(ma_structure, strength)
                logger.info(f"Confidence: {confidence}")
                
                return SignalResult(
                    strategy_name=self.config.name,
                    signal_type=signal_type.value,
                    direction=SignalDirection(direction),
                    strength=strength,
                    confidence=confidence,
                    details=ma_structure,
                    timestamp=datetime.now().isoformat(),
                    timeframe=timeframe,
                    symbol_id=symbol_id,
                    ticker=ticker,
                    exchange=exchange
                )
                
        except Exception as e:
            logger.error(f"Error evaluating SMA signal: {e}")
            return self._create_neutral_signal(symbol_id, ticker, exchange, timeframe, f"Error: {str(e)}")
    
    def get_required_indicators(self) -> List[str]:
        return ['sma_18', 'sma_36', 'sma_48', 'sma_144']
    
    def get_supported_timeframes(self) -> List[str]:
        return ['1m', '2m', '5m', '15m', '30m', '1h', '4h']
    
    def _calculate_sma_confidence(self, ma_structure: Dict, strength: float) -> float:
        """Tính confidence cho SMA signal"""
        cp = ma_structure['cp']
        m1 = ma_structure['m1']
        m2 = ma_structure['m2']
        m3 = ma_structure['m3']
        ma144 = ma_structure['ma144']
        
        # Base confidence từ strength
        base_confidence = strength
        
        # Bonus nếu MA alignment tốt
        if cp > m1 > m2 > m3:  # Bullish alignment
            base_confidence += 0.2
        elif cp < m1 < m2 < m3:  # Bearish alignment
            base_confidence += 0.2
        
        # Bonus nếu price vs MA144
        if cp > ma144:
            base_confidence += 0.1
        elif cp < ma144:
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _create_neutral_signal(self, symbol_id: int, ticker: str, exchange: str, 
                              timeframe: str, reason: str) -> SignalResult:
        """Tạo tín hiệu neutral"""
        return SignalResult(
            strategy_name=self.config.name,
            signal_type="neutral",
            direction=SignalDirection.NEUTRAL,
            strength=0.0,
            confidence=0.0,
            details={'reason': reason},
            timestamp=datetime.now().isoformat(),
            timeframe=timeframe,
            symbol_id=symbol_id,
            ticker=ticker,
            exchange=exchange
        )

class MACDStrategy(BaseStrategy):
    """MACD Strategy Implementation"""
    
    def __init__(self, config: StrategyConfig = None):
        if config is None:
            config = StrategyConfig(
                name="MACD Strategy",
                description="MACD zone-based strategy",
                version="1.0.0",
                weight=1.0,
                min_confidence=0.5,
                parameters={
                    'fast_period': 7,
                    'slow_period': 72,
                    'signal_period': 144,
                    'use_zones': True
                }
            )
        super().__init__(config)
    
    def evaluate_signal(self, symbol_id: int, ticker: str, exchange: str, 
                       timeframe: str) -> SignalResult:
        """Đánh giá tín hiệu MACD"""
        try:
            with SessionLocal() as s:
                # Lấy dữ liệu MACD mới nhất
                row = s.execute(text("""
                    SELECT ts, macd, macd_signal, hist
                    FROM indicators_macd
                    WHERE symbol_id = :symbol_id AND timeframe = :timeframe
                    ORDER BY ts DESC LIMIT 1
                """), {'symbol_id': symbol_id, 'timeframe': timeframe}).mappings().first()
                
                if not row:
                    return self._create_neutral_signal(symbol_id, ticker, exchange, timeframe, "No MACD data")
                
                # Đánh giá zones
                f_zone = match_zone_with_thresholds(row['macd'], symbol_id, timeframe, 'fmacd')
                s_zone = match_zone_with_thresholds(row['macd_signal'], symbol_id, timeframe, 'smacd')
                bars_zone = match_zone_with_thresholds(abs(row['hist']), symbol_id, timeframe, 'bars')
                
                # Tạo tín hiệu MACD
                macd_signal = make_signal(f_zone, s_zone, bars_zone)
                
                # Tính strength và confidence
                strength = self._calculate_macd_strength(f_zone, s_zone, bars_zone)
                confidence = self._calculate_macd_confidence(f_zone, s_zone, bars_zone, strength)
                
                return SignalResult(
                    strategy_name=self.config.name,
                    signal_type=macd_signal or "neutral",
                    direction=SignalDirection.BUY if macd_signal == 'BUY' else 
                             SignalDirection.SELL if macd_signal == 'SELL' else 
                             SignalDirection.NEUTRAL,
                    strength=strength,
                    confidence=confidence,
                    details={
                        'macd': float(row['macd']),
                        'macd_signal': float(row['macd_signal']),
                        'histogram': float(row['hist']),
                        'f_zone': f_zone,
                        's_zone': s_zone,
                        'bars_zone': bars_zone
                    },
                    timestamp=datetime.now().isoformat(),
                    timeframe=timeframe,
                    symbol_id=symbol_id,
                    ticker=ticker,
                    exchange=exchange
                )
                
        except Exception as e:
            logger.error(f"Error evaluating MACD signal: {e}")
            return self._create_neutral_signal(symbol_id, ticker, exchange, timeframe, f"Error: {str(e)}")
    
    def get_required_indicators(self) -> List[str]:
        return ['macd', 'macd_signal', 'macd_histogram']
    
    def get_supported_timeframes(self) -> List[str]:
        return ['1m', '2m', '5m', '15m', '30m', '1h', '4h']
    
    def _calculate_macd_strength(self, f_zone: str, s_zone: str, bars_zone: str) -> float:
        """Tính strength cho MACD signal"""
        zone_strength_map = {
            'igr': 1.0, 'greed': 0.8, 'bull': 0.6, 'pos': 0.4,
            'neutral': 0.0,
            'neg': 0.4, 'bear': 0.6, 'fear': 0.8, 'panic': 1.0
        }
        
        f_strength = zone_strength_map.get(f_zone, 0.0)
        s_strength = zone_strength_map.get(s_zone, 0.0)
        bars_strength = zone_strength_map.get(bars_zone, 0.0)
        
        return (f_strength * 0.4 + s_strength * 0.4 + bars_strength * 0.2)
    
    def _calculate_macd_confidence(self, f_zone: str, s_zone: str, bars_zone: str, strength: float) -> float:
        """Tính confidence cho MACD signal"""
        base_confidence = strength
        
        # Bonus nếu zones đồng thuận
        if f_zone in ['bull', 'strong_bull', 'greed', 'igr'] and s_zone in ['bull', 'strong_bull', 'greed', 'igr']:
            base_confidence += 0.2
        elif f_zone in ['bear', 'strong_bear', 'fear', 'panic'] and s_zone in ['bear', 'strong_bear', 'fear', 'panic']:
            base_confidence += 0.2
        
        return min(1.0, base_confidence)
    
    def _create_neutral_signal(self, symbol_id: int, ticker: str, exchange: str, 
                              timeframe: str, reason: str) -> SignalResult:
        """Tạo tín hiệu neutral"""
        return SignalResult(
            strategy_name=self.config.name,
            signal_type="neutral",
            direction=SignalDirection.NEUTRAL,
            strength=0.0,
            confidence=0.0,
            details={'reason': reason},
            timestamp=datetime.now().isoformat(),
            timeframe=timeframe,
            symbol_id=symbol_id,
            ticker=ticker,
            exchange=exchange
        )

class RSIStrategy(BaseStrategy):
    """RSI Strategy Implementation - Ví dụ strategy mới"""
    
    def __init__(self, config: StrategyConfig = None):
        if config is None:
            config = StrategyConfig(
                name="RSI Strategy",
                description="Relative Strength Index based strategy",
                version="1.0.0",
                weight=0.8,  # Trọng số thấp hơn SMA và MACD
                min_confidence=0.6,
                parameters={
                    'rsi_period': 14,
                    'overbought_level': 70,
                    'oversold_level': 30,
                    'strong_overbought': 80,
                    'strong_oversold': 20
                }
            )
        super().__init__(config)
    
    def evaluate_signal(self, symbol_id: int, ticker: str, exchange: str, 
                       timeframe: str) -> SignalResult:
        """Đánh giá tín hiệu RSI"""
        try:
            with SessionLocal() as s:
                # Lấy dữ liệu RSI mới nhất (giả sử có bảng indicators_rsi)
                row = s.execute(text("""
                    SELECT ts, rsi_value
                    FROM indicators_rsi
                    WHERE symbol_id = :symbol_id AND timeframe = :timeframe
                    ORDER BY ts DESC LIMIT 1
                """), {'symbol_id': symbol_id, 'timeframe': timeframe}).mappings().first()
                
                if not row:
                    return self._create_neutral_signal(symbol_id, ticker, exchange, timeframe, "No RSI data")
                
                rsi_value = float(row['rsi_value'])
                
                # Đánh giá tín hiệu RSI
                signal_type, direction, strength, confidence = self._evaluate_rsi_signal(rsi_value)
                
                return SignalResult(
                    strategy_name=self.config.name,
                    signal_type=signal_type,
                    direction=direction,
                    strength=strength,
                    confidence=confidence,
                    details={
                        'rsi_value': rsi_value,
                        'overbought_level': self.config.parameters['overbought_level'],
                        'oversold_level': self.config.parameters['oversold_level']
                    },
                    timestamp=datetime.now().isoformat(),
                    timeframe=timeframe,
                    symbol_id=symbol_id,
                    ticker=ticker,
                    exchange=exchange
                )
                
        except Exception as e:
            logger.error(f"Error evaluating RSI signal: {e}")
            return self._create_neutral_signal(symbol_id, ticker, exchange, timeframe, f"Error: {str(e)}")
    
    def get_required_indicators(self) -> List[str]:
        return ['rsi_14']
    
    def get_supported_timeframes(self) -> List[str]:
        return ['5m', '15m', '30m', '1h', '4h']  # RSI ít hiệu quả ở timeframe ngắn
    
    def _evaluate_rsi_signal(self, rsi_value: float) -> tuple:
        """Đánh giá tín hiệu RSI"""
        overbought = self.config.parameters['overbought_level']
        oversold = self.config.parameters['oversold_level']
        strong_overbought = self.config.parameters['strong_overbought']
        strong_oversold = self.config.parameters['strong_oversold']
        
        if rsi_value >= strong_overbought:
            return "strong_sell", SignalDirection.SELL, 0.9, 0.8
        elif rsi_value >= overbought:
            return "sell", SignalDirection.SELL, 0.7, 0.6
        elif rsi_value <= strong_oversold:
            return "strong_buy", SignalDirection.BUY, 0.9, 0.8
        elif rsi_value <= oversold:
            return "buy", SignalDirection.BUY, 0.7, 0.6
        else:
            return "neutral", SignalDirection.NEUTRAL, 0.0, 0.0
    
    def _create_neutral_signal(self, symbol_id: int, ticker: str, exchange: str, 
                              timeframe: str, reason: str) -> SignalResult:
        """Tạo tín hiệu neutral"""
        return SignalResult(
            strategy_name=self.config.name,
            signal_type="neutral",
            direction=SignalDirection.NEUTRAL,
            strength=0.0,
            confidence=0.0,
            details={'reason': reason},
            timestamp=datetime.now().isoformat(),
            timeframe=timeframe,
            symbol_id=symbol_id,
            ticker=ticker,
            exchange=exchange
        )
