#!/usr/bin/env python3
"""
Hybrid Signal Engine - Kết hợp SMA và MACD strategies
Tạo tín hiệu tổng hợp từ 2 chiến lược để tăng độ chính xác
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from datetime import datetime
import logging

from .sma_signal_engine import sma_signal_engine, SMASignalType
from .signal_engine import match_zone_with_thresholds, make_signal
from .strategy_config import get_strategy_config, StrategyConfig
from ..db import SessionLocal
from sqlalchemy import text

logger = logging.getLogger(__name__)

class HybridSignalType(Enum):
    """Loại tín hiệu hybrid"""
    STRONG_BUY = "strong_buy"           # Cả SMA và MACD đều BUY
    BUY = "buy"                         # Một trong hai BUY, một NEUTRAL
    WEAK_BUY = "weak_buy"               # Một BUY, một SELL (conflict)
    NEUTRAL = "neutral"                 # Cả hai đều NEUTRAL
    WEAK_SELL = "weak_sell"             # Một SELL, một BUY (conflict)
    SELL = "sell"                       # Một trong hai SELL, một NEUTRAL
    STRONG_SELL = "strong_sell"         # Cả SMA và MACD đều SELL

class HybridSignalEngine:
    """Engine kết hợp SMA và MACD signals"""
    
    def __init__(self):
        self.sma_engine = sma_signal_engine
        self.confidence_threshold = 0.6  # 60% confidence để tạo signal
        self.strong_signal_threshold = 0.8  # 80% confidence cho strong signal
        
    def evaluate_hybrid_signal(self, symbol_id: int, ticker: str, exchange: str, 
                              timeframe: str) -> Dict[str, Any]:
        """
        Đánh giá tín hiệu hybrid từ SMA và MACD
        
        Args:
            symbol_id: ID của symbol
            ticker: Mã cổ phiếu
            exchange: Sàn giao dịch
            timeframe: Timeframe (1m, 2m, 5m, 15m, 30m, 1h, 4h)
            
        Returns:
            Dict chứa tín hiệu hybrid và chi tiết
        """
        try:
            # 1. Lấy tín hiệu SMA
            sma_signal = self._get_sma_signal(symbol_id, timeframe)
            
            # 2. Lấy tín hiệu MACD
            macd_signal = self._get_macd_signal(symbol_id, timeframe)
            
            # 3. Kết hợp tín hiệu
            hybrid_result = self._combine_signals(sma_signal, macd_signal, timeframe)
            
            # 4. Tính confidence score
            confidence = self._calculate_confidence(sma_signal, macd_signal, hybrid_result)
            
            # 5. Tạo kết quả cuối cùng
            result = {
                'symbol_id': symbol_id,
                'ticker': ticker,
                'exchange': exchange,
                'timeframe': timeframe,
                'timestamp': datetime.now().isoformat(),
                'hybrid_signal': hybrid_result['signal_type'],
                'hybrid_direction': hybrid_result['direction'],
                'hybrid_strength': hybrid_result['strength'],
                'confidence': confidence,
                'sma_signal': sma_signal,
                'macd_signal': macd_signal,
                'details': {
                    'sma_details': sma_signal.get('details', {}),
                    'macd_details': macd_signal.get('details', {}),
                    'combination_logic': hybrid_result['logic']
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating hybrid signal for {ticker} {timeframe}: {e}")
            return self._create_error_result(symbol_id, ticker, exchange, timeframe, str(e))
    
    def _get_sma_signal(self, symbol_id: int, timeframe: str) -> Dict[str, Any]:
        """Lấy tín hiệu SMA"""
        try:
            with SessionLocal() as s:
                # Lấy dữ liệu SMA mới nhất
                row = s.execute(text("""
                    SELECT ts, close, m1, m2, m3, ma144, avg_m1_m2_m3
                    FROM indicators_sma
                    WHERE symbol_id = :symbol_id AND timeframe = :timeframe
                    ORDER BY ts DESC LIMIT 1
                """), {'symbol_id': symbol_id, 'timeframe': timeframe}).mappings().first()
                
                if not row:
                    return self._create_neutral_signal('SMA', 'No SMA data available')
                
                # Tạo MA structure
                ma_structure = {
                    'cp': float(row['close']),
                    'm1': float(row['m1']),
                    'm2': float(row['m2']),
                    'm3': float(row['m3']),
                    'ma144': float(row['ma144']),
                    'avg_m1_m2_m3': float(row['avg_m1_m2_m3'])
                }
                
                # Đánh giá tín hiệu SMA
                signal_type = self.sma_engine.evaluate_single_timeframe(ma_structure)
                direction = self.sma_engine.get_signal_direction(signal_type)
                strength = self.sma_engine.get_signal_strength(signal_type)
                
                return {
                    'signal_type': signal_type.value,
                    'direction': direction,
                    'strength': strength,
                    'details': ma_structure,
                    'source': 'SMA'
                }
                
        except Exception as e:
            logger.error(f"Error getting SMA signal: {e}")
            return self._create_neutral_signal('SMA', f'Error: {str(e)}')
    
    def _get_macd_signal(self, symbol_id: int, timeframe: str) -> Dict[str, Any]:
        """Lấy tín hiệu MACD"""
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
                    return self._create_neutral_signal('MACD', 'No MACD data available')
                
                # Đánh giá zones
                f_zone = match_zone_with_thresholds(row['macd'], symbol_id, timeframe, 'fmacd')
                s_zone = match_zone_with_thresholds(row['macd_signal'], symbol_id, timeframe, 'smacd')
                bars_zone = match_zone_with_thresholds(abs(row['hist']), symbol_id, timeframe, 'bars')
                
                # Tạo tín hiệu MACD
                macd_signal = make_signal(f_zone, s_zone, bars_zone)
                
                # Tính strength dựa trên zones
                strength = self._calculate_macd_strength(f_zone, s_zone, bars_zone)
                
                return {
                    'signal_type': macd_signal or 'NEUTRAL',
                    'direction': 'BUY' if macd_signal == 'BUY' else 'SELL' if macd_signal == 'SELL' else 'NEUTRAL',
                    'strength': strength,
                    'details': {
                        'macd': float(row['macd']),
                        'macd_signal': float(row['macd_signal']),
                        'histogram': float(row['hist']),
                        'f_zone': f_zone,
                        's_zone': s_zone,
                        'bars_zone': bars_zone
                    },
                    'source': 'MACD'
                }
                
        except Exception as e:
            logger.error(f"Error getting MACD signal: {e}")
            return self._create_neutral_signal('MACD', f'Error: {str(e)}')
    
    def _combine_signals(self, sma_signal: Dict, macd_signal: Dict, timeframe: str) -> Dict[str, Any]:
        """Kết hợp tín hiệu SMA và MACD"""
        
        sma_direction = sma_signal.get('direction', 'NEUTRAL')
        macd_direction = macd_signal.get('direction', 'NEUTRAL')
        sma_strength = sma_signal.get('strength', 0.0)
        macd_strength = macd_signal.get('strength', 0.0)
        
        # Logic kết hợp
        if sma_direction == 'BUY' and macd_direction == 'BUY':
            signal_type = HybridSignalType.STRONG_BUY
            direction = 'BUY'
            strength = min(sma_strength + macd_strength, 1.0)
            logic = "Both SMA and MACD bullish"
            
        elif sma_direction == 'SELL' and macd_direction == 'SELL':
            signal_type = HybridSignalType.STRONG_SELL
            direction = 'SELL'
            strength = min(sma_strength + macd_strength, 1.0)
            logic = "Both SMA and MACD bearish"
            
        elif sma_direction == 'BUY' and macd_direction == 'NEUTRAL':
            signal_type = HybridSignalType.BUY
            direction = 'BUY'
            strength = sma_strength * 0.7  # Giảm strength vì chỉ có SMA
            logic = "SMA bullish, MACD neutral"
            
        elif sma_direction == 'NEUTRAL' and macd_direction == 'BUY':
            signal_type = HybridSignalType.BUY
            direction = 'BUY'
            strength = macd_strength * 0.7  # Giảm strength vì chỉ có MACD
            logic = "MACD bullish, SMA neutral"
            
        elif sma_direction == 'SELL' and macd_direction == 'NEUTRAL':
            signal_type = HybridSignalType.SELL
            direction = 'SELL'
            strength = sma_strength * 0.7
            logic = "SMA bearish, MACD neutral"
            
        elif sma_direction == 'NEUTRAL' and macd_direction == 'SELL':
            signal_type = HybridSignalType.SELL
            direction = 'SELL'
            strength = macd_strength * 0.7
            logic = "MACD bearish, SMA neutral"
            
        elif sma_direction == 'BUY' and macd_direction == 'SELL':
            signal_type = HybridSignalType.WEAK_BUY
            direction = 'BUY'
            strength = abs(sma_strength - macd_strength) * 0.3  # Rất yếu vì conflict
            logic = "SMA bullish, MACD bearish (conflict)"
            
        elif sma_direction == 'SELL' and macd_direction == 'BUY':
            signal_type = HybridSignalType.WEAK_SELL
            direction = 'SELL'
            strength = abs(sma_strength - macd_strength) * 0.3
            logic = "SMA bearish, MACD bullish (conflict)"
            
        else:  # Cả hai đều NEUTRAL
            signal_type = HybridSignalType.NEUTRAL
            direction = 'NEUTRAL'
            strength = 0.0
            logic = "Both SMA and MACD neutral"
        
        return {
            'signal_type': signal_type,
            'direction': direction,
            'strength': strength,
            'logic': logic
        }
    
    def _calculate_confidence(self, sma_signal: Dict, macd_signal: Dict, hybrid_result: Dict) -> float:
        """Tính confidence score cho tín hiệu hybrid"""
        
        sma_strength = sma_signal.get('strength', 0.0)
        macd_strength = macd_signal.get('strength', 0.0)
        hybrid_strength = hybrid_result.get('strength', 0.0)
        
        # Base confidence từ strength
        base_confidence = hybrid_strength
        
        # Bonus confidence nếu cả hai strategies đồng thuận
        if (sma_signal.get('direction') == macd_signal.get('direction') and 
            sma_signal.get('direction') != 'NEUTRAL'):
            base_confidence += 0.2  # +20% bonus
        
        # Penalty nếu có conflict
        if (sma_signal.get('direction') != macd_signal.get('direction') and 
            sma_signal.get('direction') != 'NEUTRAL' and 
            macd_signal.get('direction') != 'NEUTRAL'):
            base_confidence -= 0.3  # -30% penalty
        
        return max(0.0, min(1.0, base_confidence))
    
    def _calculate_macd_strength(self, f_zone: str, s_zone: str, bars_zone: str) -> float:
        """Tính strength cho MACD signal dựa trên zones"""
        
        zone_strength_map = {
            'igr': 1.0, 'greed': 0.8, 'bull': 0.6, 'pos': 0.4,
            'neutral': 0.0,
            'neg': 0.4, 'bear': 0.6, 'fear': 0.8, 'panic': 1.0
        }
        
        f_strength = zone_strength_map.get(f_zone, 0.0)
        s_strength = zone_strength_map.get(s_zone, 0.0)
        bars_strength = zone_strength_map.get(bars_zone, 0.0)
        
        # Trung bình có trọng số
        return (f_strength * 0.4 + s_strength * 0.4 + bars_strength * 0.2)
    
    def _create_neutral_signal(self, source: str, reason: str) -> Dict[str, Any]:
        """Tạo tín hiệu neutral"""
        return {
            'signal_type': 'NEUTRAL',
            'direction': 'NEUTRAL',
            'strength': 0.0,
            'details': {'reason': reason},
            'source': source
        }
    
    def _create_error_result(self, symbol_id: int, ticker: str, exchange: str, 
                           timeframe: str, error: str) -> Dict[str, Any]:
        """Tạo kết quả lỗi"""
        return {
            'symbol_id': symbol_id,
            'ticker': ticker,
            'exchange': exchange,
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat(),
            'hybrid_signal': 'ERROR',
            'hybrid_direction': 'NEUTRAL',
            'hybrid_strength': 0.0,
            'confidence': 0.0,
            'error': error,
            'sma_signal': self._create_neutral_signal('SMA', 'Error'),
            'macd_signal': self._create_neutral_signal('MACD', 'Error')
        }
    
    def evaluate_multi_timeframe_hybrid(self, symbol_id: int, ticker: str, exchange: str) -> Dict[str, Any]:
        """Đánh giá tín hiệu hybrid cho nhiều timeframes"""
        
        timeframes = ['1m', '2m', '5m', '15m', '30m', '1h', '4h']
        timeframe_results = {}
        
        for tf in timeframes:
            try:
                result = self.evaluate_hybrid_signal(symbol_id, ticker, exchange, tf)
                timeframe_results[tf] = result
            except Exception as e:
                logger.error(f"Error evaluating {tf} for {ticker}: {e}")
                timeframe_results[tf] = self._create_error_result(symbol_id, ticker, exchange, tf, str(e))
        
        # Tổng hợp kết quả multi-timeframe
        return self._aggregate_multi_timeframe_results(timeframe_results)
    
    def _aggregate_multi_timeframe_results(self, timeframe_results: Dict[str, Any]) -> Dict[str, Any]:
        """Tổng hợp kết quả từ nhiều timeframes"""
        
        # Trọng số cho từng timeframe
        tf_weights = {
            '1m': 1, '2m': 2, '5m': 3, '15m': 4, 
            '30m': 5, '1h': 6, '4h': 7
        }
        
        total_weight = 0
        weighted_buy_score = 0
        weighted_sell_score = 0
        weighted_confidence = 0
        
        for tf, result in timeframe_results.items():
            if result.get('error'):
                continue
                
            weight = tf_weights.get(tf, 1)
            direction = result.get('hybrid_direction', 'NEUTRAL')
            strength = result.get('hybrid_strength', 0.0)
            confidence = result.get('confidence', 0.0)
            
            total_weight += weight
            
            if direction == 'BUY':
                weighted_buy_score += weight * strength
            elif direction == 'SELL':
                weighted_sell_score += weight * strength
            
            weighted_confidence += weight * confidence
        
        if total_weight == 0:
            return {
                'overall_signal': 'NEUTRAL',
                'overall_direction': 'NEUTRAL',
                'overall_strength': 0.0,
                'overall_confidence': 0.0,
                'timeframe_results': timeframe_results
            }
        
        # Xác định tín hiệu tổng thể
        buy_ratio = weighted_buy_score / total_weight
        sell_ratio = weighted_sell_score / total_weight
        overall_confidence = weighted_confidence / total_weight
        
        if buy_ratio > sell_ratio and buy_ratio > 0.3:
            overall_direction = 'BUY'
            overall_strength = buy_ratio
        elif sell_ratio > buy_ratio and sell_ratio > 0.3:
            overall_direction = 'SELL'
            overall_strength = sell_ratio
        else:
            overall_direction = 'NEUTRAL'
            overall_strength = 0.0
        
        return {
            'overall_signal': f"{overall_direction}_{overall_strength:.2f}",
            'overall_direction': overall_direction,
            'overall_strength': overall_strength,
            'overall_confidence': overall_confidence,
            'timeframe_results': timeframe_results,
            'buy_ratio': buy_ratio,
            'sell_ratio': sell_ratio
        }

# Global instance
hybrid_signal_engine = HybridSignalEngine()
