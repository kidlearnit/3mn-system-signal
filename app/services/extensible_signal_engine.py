#!/usr/bin/env python3
"""
Extensible Signal Engine - Engine tín hiệu có thể mở rộng
Thay thế cho hybrid_signal_engine với khả năng mở rộng không giới hạn
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from .strategy_base import strategy_registry, BaseStrategy
from .strategy_implementations import SMAStrategy, MACDStrategy, RSIStrategy
from .aggregation_engine import aggregation_engine, AggregationConfig, AggregationMethod
from ..db import init_db
from sqlalchemy import text
import os

# Initialize database
init_db(os.getenv("DATABASE_URL"))

# Import SessionLocal after initialization
from ..db import SessionLocal

logger = logging.getLogger(__name__)

class ExtensibleSignalEngine:
    """Engine tín hiệu có thể mở rộng với nhiều strategies"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._initialize_default_strategies()
    
    def _initialize_default_strategies(self):
        """Khởi tạo các strategies mặc định"""
        try:
            # Đăng ký các strategies mặc định
            sma_strategy = SMAStrategy()
            macd_strategy = MACDStrategy()
            rsi_strategy = RSIStrategy()
            
            strategy_registry.register_strategy(sma_strategy)
            strategy_registry.register_strategy(macd_strategy)
            strategy_registry.register_strategy(rsi_strategy)
            
            self.logger.info("Initialized default strategies: SMA, MACD, RSI")
            
        except Exception as e:
            self.logger.error(f"Error initializing default strategies: {e}")
    
    def evaluate_signal(self, symbol_id: int, ticker: str, exchange: str, 
                       timeframe: str, strategy_names: List[str] = None) -> Dict[str, Any]:
        """
        Đánh giá tín hiệu từ các strategies được chỉ định
        
        Args:
            symbol_id: ID của symbol
            ticker: Mã cổ phiếu
            exchange: Sàn giao dịch
            timeframe: Timeframe
            strategy_names: Danh sách tên strategies (None = tất cả active)
            
        Returns:
            Dict chứa kết quả tín hiệu đã tổng hợp
        """
        try:
            # Lấy danh sách strategies để đánh giá
            if strategy_names is None:
                strategies = strategy_registry.get_active_strategies()
            else:
                strategies = [strategy_registry.get_strategy(name) 
                            for name in strategy_names 
                            if strategy_registry.get_strategy(name)]
            
            if not strategies:
                return self._create_error_result(symbol_id, ticker, exchange, timeframe, 
                                               "No active strategies found")
            
            # Đánh giá tín hiệu từ từng strategy
            strategy_results = []
            for strategy in strategies:
                try:
                    result = strategy.evaluate_signal(symbol_id, ticker, exchange, timeframe)
                    if strategy.is_signal_valid(result):
                        strategy_results.append(result)
                except Exception as e:
                    self.logger.error(f"Error evaluating {strategy.config.name}: {e}")
                    continue
            
            if not strategy_results:
                return self._create_error_result(symbol_id, ticker, exchange, timeframe, 
                                               "No valid strategy results")
            
            # Tổng hợp tín hiệu
            aggregated_signal = aggregation_engine.aggregate_signals(
                strategy_results, symbol_id, ticker, exchange, timeframe
            )
            
            # Tạo kết quả cuối cùng
            return {
                'symbol_id': symbol_id,
                'ticker': ticker,
                'exchange': exchange,
                'timeframe': timeframe,
                'timestamp': datetime.now().isoformat(),
                'final_signal': aggregated_signal.final_signal,
                'final_direction': aggregated_signal.final_direction.value,
                'final_strength': aggregated_signal.final_strength,
                'final_confidence': aggregated_signal.final_confidence,
                'participating_strategies': aggregated_signal.participating_strategies,
                'strategy_results': {
                    name: {
                        'signal_type': result.signal_type,
                        'direction': result.direction.value,
                        'strength': result.strength,
                        'confidence': result.confidence,
                        'details': result.details
                    }
                    for name, result in aggregated_signal.strategy_results.items()
                },
                'aggregation_details': aggregated_signal.aggregation_details
            }
            
        except Exception as e:
            self.logger.error(f"Error evaluating extensible signal: {e}")
            return self._create_error_result(symbol_id, ticker, exchange, timeframe, str(e))
    
    def evaluate_multi_timeframe(self, symbol_id: int, ticker: str, exchange: str,
                               strategy_names: List[str] = None) -> Dict[str, Any]:
        """
        Đánh giá tín hiệu multi-timeframe
        
        Args:
            symbol_id: ID của symbol
            ticker: Mã cổ phiếu
            exchange: Sàn giao dịch
            strategy_names: Danh sách tên strategies
            
        Returns:
            Dict chứa kết quả multi-timeframe
        """
        try:
            timeframes = ['1m', '2m', '5m', '15m', '30m', '1h', '4h']
            timeframe_results = {}
            
            for tf in timeframes:
                try:
                    result = self.evaluate_signal(symbol_id, ticker, exchange, tf, strategy_names)
                    timeframe_results[tf] = result
                except Exception as e:
                    self.logger.error(f"Error evaluating {tf} for {ticker}: {e}")
                    timeframe_results[tf] = self._create_error_result(symbol_id, ticker, exchange, tf, str(e))
            
            # Tổng hợp kết quả multi-timeframe
            return self._aggregate_multi_timeframe_results(timeframe_results)
            
        except Exception as e:
            self.logger.error(f"Error in multi-timeframe evaluation: {e}")
            return self._create_error_result(symbol_id, ticker, exchange, "multi", str(e))
    
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
        
        valid_timeframes = 0
        
        for tf, result in timeframe_results.items():
            if result.get('error'):
                continue
                
            weight = tf_weights.get(tf, 1)
            direction = result.get('final_direction', 'NEUTRAL')
            strength = result.get('final_strength', 0.0)
            confidence = result.get('final_confidence', 0.0)
            
            total_weight += weight
            valid_timeframes += 1
            
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
                'timeframe_results': timeframe_results,
                'error': 'No valid timeframe results'
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
            'sell_ratio': sell_ratio,
            'valid_timeframes': valid_timeframes,
            'total_timeframes': len(timeframe_results)
        }
    
    def add_strategy(self, strategy: BaseStrategy) -> bool:
        """
        Thêm strategy mới
        
        Args:
            strategy: Strategy instance
            
        Returns:
            bool: True nếu thêm thành công
        """
        return strategy_registry.register_strategy(strategy)
    
    def remove_strategy(self, strategy_name: str) -> bool:
        """
        Xóa strategy
        
        Args:
            strategy_name: Tên strategy
            
        Returns:
            bool: True nếu xóa thành công
        """
        return strategy_registry.unregister_strategy(strategy_name)
    
    def get_available_strategies(self) -> List[str]:
        """Lấy danh sách strategies có sẵn"""
        return strategy_registry.get_strategy_names()
    
    def get_strategy_info(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin strategy"""
        return strategy_registry.get_strategy_info(strategy_name)
    
    def update_aggregation_config(self, config: AggregationConfig):
        """Cập nhật cấu hình aggregation"""
        aggregation_engine.update_config(config)
    
    def get_aggregation_info(self) -> Dict[str, Any]:
        """Lấy thông tin aggregation engine"""
        return aggregation_engine.get_aggregation_info()
    
    def _create_error_result(self, symbol_id: int, ticker: str, exchange: str, 
                           timeframe: str, error: str) -> Dict[str, Any]:
        """Tạo kết quả lỗi"""
        return {
            'symbol_id': symbol_id,
            'ticker': ticker,
            'exchange': exchange,
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat(),
            'final_signal': 'ERROR',
            'final_direction': 'NEUTRAL',
            'final_strength': 0.0,
            'final_confidence': 0.0,
            'error': error,
            'participating_strategies': [],
            'strategy_results': {},
            'aggregation_details': {'error': error}
        }

# Global extensible signal engine
extensible_signal_engine = ExtensibleSignalEngine()
