#!/usr/bin/env python3
"""
Aggregation Engine - Engine tổng hợp tín hiệu từ nhiều strategies
"""

from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import logging

from .strategy_base import BaseStrategy, SignalResult, SignalDirection, strategy_registry

logger = logging.getLogger(__name__)

class AggregationMethod(Enum):
    """Phương pháp tổng hợp tín hiệu"""
    WEIGHTED_AVERAGE = "weighted_average"
    MAJORITY_VOTE = "majority_vote"
    CONSENSUS = "consensus"
    CONFIDENCE_WEIGHTED = "confidence_weighted"
    CUSTOM = "custom"

@dataclass
class AggregationConfig:
    """Cấu hình cho aggregation engine"""
    method: AggregationMethod = AggregationMethod.WEIGHTED_AVERAGE
    min_strategies: int = 2  # Số strategies tối thiểu để tạo signal
    consensus_threshold: float = 0.6  # Ngưỡng consensus (60%)
    confidence_threshold: float = 0.5  # Ngưỡng confidence tối thiểu
    conflict_penalty: float = 0.3  # Penalty khi có conflict
    custom_weights: Dict[str, float] = None  # Trọng số tùy chỉnh
    
    def __post_init__(self):
        if self.custom_weights is None:
            self.custom_weights = {}

@dataclass
class AggregatedSignal:
    """Tín hiệu đã được tổng hợp"""
    final_signal: str
    final_direction: SignalDirection
    final_strength: float
    final_confidence: float
    participating_strategies: List[str]
    strategy_results: Dict[str, SignalResult]
    aggregation_details: Dict[str, Any]
    timestamp: str
    symbol_id: int
    ticker: str
    exchange: str
    timeframe: str

class AggregationEngine:
    """Engine tổng hợp tín hiệu từ nhiều strategies"""
    
    def __init__(self, config: AggregationConfig = None):
        self.config = config or AggregationConfig()
        self.logger = logging.getLogger(__name__)
    
    def aggregate_signals(self, strategy_results: List[SignalResult], 
                         symbol_id: int, ticker: str, exchange: str, 
                         timeframe: str) -> AggregatedSignal:
        """
        Tổng hợp tín hiệu từ nhiều strategies
        
        Args:
            strategy_results: Danh sách kết quả từ các strategies
            symbol_id: ID của symbol
            ticker: Mã cổ phiếu
            exchange: Sàn giao dịch
            timeframe: Timeframe
            
        Returns:
            AggregatedSignal: Tín hiệu đã được tổng hợp
        """
        if len(strategy_results) < self.config.min_strategies:
            return self._create_neutral_aggregated_signal(
                strategy_results, symbol_id, ticker, exchange, timeframe,
                f"Not enough strategies (need {self.config.min_strategies}, got {len(strategy_results)})"
            )
        
        # Lọc strategies có confidence đủ cao
        valid_results = [r for r in strategy_results 
                        if r.confidence >= self.config.confidence_threshold]
        
        if len(valid_results) < self.config.min_strategies:
            return self._create_neutral_aggregated_signal(
                strategy_results, symbol_id, ticker, exchange, timeframe,
                f"Not enough high-confidence strategies"
            )
        
        # Tổng hợp theo phương pháp được chọn
        if self.config.method == AggregationMethod.WEIGHTED_AVERAGE:
            return self._weighted_average_aggregation(valid_results, symbol_id, ticker, exchange, timeframe)
        elif self.config.method == AggregationMethod.MAJORITY_VOTE:
            return self._majority_vote_aggregation(valid_results, symbol_id, ticker, exchange, timeframe)
        elif self.config.method == AggregationMethod.CONSENSUS:
            return self._consensus_aggregation(valid_results, symbol_id, ticker, exchange, timeframe)
        elif self.config.method == AggregationMethod.CONFIDENCE_WEIGHTED:
            return self._confidence_weighted_aggregation(valid_results, symbol_id, ticker, exchange, timeframe)
        else:
            return self._weighted_average_aggregation(valid_results, symbol_id, ticker, exchange, timeframe)
    
    def _weighted_average_aggregation(self, results: List[SignalResult], 
                                    symbol_id: int, ticker: str, exchange: str, 
                                    timeframe: str) -> AggregatedSignal:
        """Tổng hợp theo trọng số trung bình"""
        
        total_weight = 0
        weighted_buy_score = 0
        weighted_sell_score = 0
        weighted_confidence = 0
        
        strategy_details = {}
        
        for result in results:
            # Lấy trọng số từ strategy config hoặc custom weights
            strategy = strategy_registry.get_strategy(result.strategy_name)
            weight = self.config.custom_weights.get(result.strategy_name, 
                                                   strategy.config.weight if strategy else 1.0)
            
            total_weight += weight
            
            if result.direction == SignalDirection.BUY:
                weighted_buy_score += weight * result.strength
            elif result.direction == SignalDirection.SELL:
                weighted_sell_score += weight * result.strength
            
            weighted_confidence += weight * result.confidence
            
            strategy_details[result.strategy_name] = {
                'weight': weight,
                'strength': result.strength,
                'confidence': result.confidence,
                'direction': result.direction.value
            }
        
        if total_weight == 0:
            return self._create_neutral_aggregated_signal(
                results, symbol_id, ticker, exchange, timeframe, "No valid weights"
            )
        
        # Tính điểm cuối cùng
        buy_ratio = weighted_buy_score / total_weight
        sell_ratio = weighted_sell_score / total_weight
        final_confidence = weighted_confidence / total_weight
        
        # Xác định tín hiệu cuối cùng
        if buy_ratio > sell_ratio and buy_ratio > 0.3:
            final_direction = SignalDirection.BUY
            final_strength = buy_ratio
            final_signal = "buy"
        elif sell_ratio > buy_ratio and sell_ratio > 0.3:
            final_direction = SignalDirection.SELL
            final_strength = sell_ratio
            final_signal = "sell"
        else:
            final_direction = SignalDirection.NEUTRAL
            final_strength = 0.0
            final_signal = "neutral"
        
        return AggregatedSignal(
            final_signal=final_signal,
            final_direction=final_direction,
            final_strength=final_strength,
            final_confidence=final_confidence,
            participating_strategies=[r.strategy_name for r in results],
            strategy_results={r.strategy_name: r for r in results},
            aggregation_details={
                'method': 'weighted_average',
                'total_weight': total_weight,
                'buy_ratio': buy_ratio,
                'sell_ratio': sell_ratio,
                'strategy_details': strategy_details
            },
            timestamp=datetime.now().isoformat(),
            symbol_id=symbol_id,
            ticker=ticker,
            exchange=exchange,
            timeframe=timeframe
        )
    
    def _majority_vote_aggregation(self, results: List[SignalResult], 
                                 symbol_id: int, ticker: str, exchange: str, 
                                 timeframe: str) -> AggregatedSignal:
        """Tổng hợp theo majority vote"""
        
        buy_votes = 0
        sell_votes = 0
        neutral_votes = 0
        
        total_confidence = 0
        total_strength = 0
        
        for result in results:
            if result.direction == SignalDirection.BUY:
                buy_votes += 1
            elif result.direction == SignalDirection.SELL:
                sell_votes += 1
            else:
                neutral_votes += 1
            
            total_confidence += result.confidence
            total_strength += result.strength
        
        total_votes = len(results)
        avg_confidence = total_confidence / total_votes
        avg_strength = total_strength / total_votes
        
        # Xác định tín hiệu theo majority
        if buy_votes > sell_votes and buy_votes > neutral_votes:
            final_direction = SignalDirection.BUY
            final_signal = "buy"
            final_strength = avg_strength * (buy_votes / total_votes)
        elif sell_votes > buy_votes and sell_votes > neutral_votes:
            final_direction = SignalDirection.SELL
            final_signal = "sell"
            final_strength = avg_strength * (sell_votes / total_votes)
        else:
            final_direction = SignalDirection.NEUTRAL
            final_signal = "neutral"
            final_strength = 0.0
        
        return AggregatedSignal(
            final_signal=final_signal,
            final_direction=final_direction,
            final_strength=final_strength,
            final_confidence=avg_confidence,
            participating_strategies=[r.strategy_name for r in results],
            strategy_results={r.strategy_name: r for r in results},
            aggregation_details={
                'method': 'majority_vote',
                'buy_votes': buy_votes,
                'sell_votes': sell_votes,
                'neutral_votes': neutral_votes,
                'total_votes': total_votes
            },
            timestamp=datetime.now().isoformat(),
            symbol_id=symbol_id,
            ticker=ticker,
            exchange=exchange,
            timeframe=timeframe
        )
    
    def _consensus_aggregation(self, results: List[SignalResult], 
                             symbol_id: int, ticker: str, exchange: str, 
                             timeframe: str) -> AggregatedSignal:
        """Tổng hợp theo consensus"""
        
        # Đếm votes cho mỗi direction
        direction_votes = {}
        total_confidence = 0
        total_strength = 0
        
        for result in results:
            direction = result.direction.value
            if direction not in direction_votes:
                direction_votes[direction] = {'count': 0, 'confidence': 0, 'strength': 0}
            
            direction_votes[direction]['count'] += 1
            direction_votes[direction]['confidence'] += result.confidence
            direction_votes[direction]['strength'] += result.strength
            
            total_confidence += result.confidence
            total_strength += result.strength
        
        # Tìm direction có consensus cao nhất
        max_consensus = 0
        final_direction = SignalDirection.NEUTRAL
        final_signal = "neutral"
        final_strength = 0.0
        
        for direction, votes in direction_votes.items():
            consensus_ratio = votes['count'] / len(results)
            if consensus_ratio > max_consensus and consensus_ratio >= self.config.consensus_threshold:
                max_consensus = consensus_ratio
                final_direction = SignalDirection(direction)
                final_signal = direction.lower()
                final_strength = votes['strength'] / votes['count']
        
        final_confidence = total_confidence / len(results)
        
        return AggregatedSignal(
            final_signal=final_signal,
            final_direction=final_direction,
            final_strength=final_strength,
            final_confidence=final_confidence,
            participating_strategies=[r.strategy_name for r in results],
            strategy_results={r.strategy_name: r for r in results},
            aggregation_details={
                'method': 'consensus',
                'consensus_threshold': self.config.consensus_threshold,
                'direction_votes': direction_votes,
                'max_consensus': max_consensus
            },
            timestamp=datetime.now().isoformat(),
            symbol_id=symbol_id,
            ticker=ticker,
            exchange=exchange,
            timeframe=timeframe
        )
    
    def _confidence_weighted_aggregation(self, results: List[SignalResult], 
                                       symbol_id: int, ticker: str, exchange: str, 
                                       timeframe: str) -> AggregatedSignal:
        """Tổng hợp theo confidence weight"""
        
        total_confidence_weight = 0
        confidence_weighted_buy = 0
        confidence_weighted_sell = 0
        total_confidence = 0
        
        for result in results:
            confidence_weight = result.confidence
            total_confidence_weight += confidence_weight
            total_confidence += result.confidence
            
            if result.direction == SignalDirection.BUY:
                confidence_weighted_buy += confidence_weight * result.strength
            elif result.direction == SignalDirection.SELL:
                confidence_weighted_sell += confidence_weight * result.strength
        
        if total_confidence_weight == 0:
            return self._create_neutral_aggregated_signal(
                results, symbol_id, ticker, exchange, timeframe, "No confidence weights"
            )
        
        buy_ratio = confidence_weighted_buy / total_confidence_weight
        sell_ratio = confidence_weighted_sell / total_confidence_weight
        final_confidence = total_confidence / len(results)
        
        if buy_ratio > sell_ratio and buy_ratio > 0.3:
            final_direction = SignalDirection.BUY
            final_strength = buy_ratio
            final_signal = "buy"
        elif sell_ratio > buy_ratio and sell_ratio > 0.3:
            final_direction = SignalDirection.SELL
            final_strength = sell_ratio
            final_signal = "sell"
        else:
            final_direction = SignalDirection.NEUTRAL
            final_strength = 0.0
            final_signal = "neutral"
        
        return AggregatedSignal(
            final_signal=final_signal,
            final_direction=final_direction,
            final_strength=final_strength,
            final_confidence=final_confidence,
            participating_strategies=[r.strategy_name for r in results],
            strategy_results={r.strategy_name: r for r in results},
            aggregation_details={
                'method': 'confidence_weighted',
                'total_confidence_weight': total_confidence_weight,
                'buy_ratio': buy_ratio,
                'sell_ratio': sell_ratio
            },
            timestamp=datetime.now().isoformat(),
            symbol_id=symbol_id,
            ticker=ticker,
            exchange=exchange,
            timeframe=timeframe
        )
    
    def _create_neutral_aggregated_signal(self, results: List[SignalResult], 
                                        symbol_id: int, ticker: str, exchange: str, 
                                        timeframe: str, reason: str) -> AggregatedSignal:
        """Tạo tín hiệu neutral"""
        return AggregatedSignal(
            final_signal="neutral",
            final_direction=SignalDirection.NEUTRAL,
            final_strength=0.0,
            final_confidence=0.0,
            participating_strategies=[r.strategy_name for r in results],
            strategy_results={r.strategy_name: r for r in results},
            aggregation_details={
                'method': 'neutral',
                'reason': reason
            },
            timestamp=datetime.now().isoformat(),
            symbol_id=symbol_id,
            ticker=ticker,
            exchange=exchange,
            timeframe=timeframe
        )
    
    def update_config(self, new_config: AggregationConfig):
        """Cập nhật cấu hình aggregation"""
        self.config = new_config
        self.logger.info(f"Updated aggregation config: {new_config.method.value}")
    
    def get_aggregation_info(self) -> Dict[str, Any]:
        """Lấy thông tin về aggregation engine"""
        return {
            'method': self.config.method.value,
            'min_strategies': self.config.min_strategies,
            'consensus_threshold': self.config.consensus_threshold,
            'confidence_threshold': self.config.confidence_threshold,
            'conflict_penalty': self.config.conflict_penalty,
            'custom_weights': self.config.custom_weights
        }

# Global aggregation engine
aggregation_engine = AggregationEngine()
