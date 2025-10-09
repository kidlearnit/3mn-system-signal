#!/usr/bin/env python3
"""
Strategy Base Classes - Thiết kế mở rộng cho các chiến lược trading
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

class SignalDirection(Enum):
    """Hướng tín hiệu"""
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"

class SignalStrength(Enum):
    """Độ mạnh tín hiệu"""
    VERY_WEAK = 0.1
    WEAK = 0.3
    MEDIUM = 0.5
    STRONG = 0.7
    VERY_STRONG = 0.9

@dataclass
class SignalResult:
    """Kết quả tín hiệu từ một strategy"""
    strategy_name: str
    signal_type: str
    direction: SignalDirection
    strength: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0
    details: Dict[str, Any]
    timestamp: str
    timeframe: str
    symbol_id: int
    ticker: str
    exchange: str

@dataclass
class StrategyConfig:
    """Cấu hình cho strategy"""
    name: str
    description: str
    version: str
    is_active: bool = True
    weight: float = 1.0  # Trọng số trong aggregation
    min_confidence: float = 0.5  # Confidence tối thiểu để tạo signal
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}

class BaseStrategy(ABC):
    """Base class cho tất cả các strategies"""
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def evaluate_signal(self, symbol_id: int, ticker: str, exchange: str, 
                       timeframe: str) -> SignalResult:
        """
        Đánh giá tín hiệu cho một symbol và timeframe
        
        Args:
            symbol_id: ID của symbol
            ticker: Mã cổ phiếu
            exchange: Sàn giao dịch
            timeframe: Timeframe (1m, 2m, 5m, 15m, 30m, 1h, 4h)
            
        Returns:
            SignalResult: Kết quả tín hiệu
        """
        pass
    
    @abstractmethod
    def get_required_indicators(self) -> List[str]:
        """
        Lấy danh sách indicators cần thiết cho strategy
        
        Returns:
            List[str]: Danh sách tên indicators
        """
        pass
    
    @abstractmethod
    def get_supported_timeframes(self) -> List[str]:
        """
        Lấy danh sách timeframes được hỗ trợ
        
        Returns:
            List[str]: Danh sách timeframes
        """
        pass
    
    def validate_config(self) -> bool:
        """
        Validate cấu hình strategy
        
        Returns:
            bool: True nếu config hợp lệ
        """
        if not self.config.name:
            self.logger.error("Strategy name is required")
            return False
        
        if self.config.weight < 0 or self.config.weight > 2.0:
            self.logger.error("Strategy weight must be between 0 and 2.0")
            return False
        
        if self.config.min_confidence < 0 or self.config.min_confidence > 1.0:
            self.logger.error("Min confidence must be between 0 and 1.0")
            return False
        
        return True
    
    def is_signal_valid(self, signal_result: SignalResult) -> bool:
        """
        Kiểm tra xem tín hiệu có hợp lệ không
        
        Args:
            signal_result: Kết quả tín hiệu
            
        Returns:
            bool: True nếu tín hiệu hợp lệ
        """
        return (signal_result.confidence >= self.config.min_confidence and
                signal_result.strength > 0.0)
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Lấy thông tin về strategy
        
        Returns:
            Dict[str, Any]: Thông tin strategy
        """
        return {
            'name': self.config.name,
            'description': self.config.description,
            'version': self.config.version,
            'is_active': self.config.is_active,
            'weight': self.config.weight,
            'min_confidence': self.config.min_confidence,
            'required_indicators': self.get_required_indicators(),
            'supported_timeframes': self.get_supported_timeframes(),
            'parameters': self.config.parameters
        }

class StrategyRegistry:
    """Registry để quản lý các strategies"""
    
    def __init__(self):
        self._strategies: Dict[str, BaseStrategy] = {}
        self._strategy_configs: Dict[str, StrategyConfig] = {}
        self.logger = logging.getLogger(f"{__name__}.StrategyRegistry")
    
    def register_strategy(self, strategy: BaseStrategy) -> bool:
        """
        Đăng ký một strategy
        
        Args:
            strategy: Strategy instance
            
        Returns:
            bool: True nếu đăng ký thành công
        """
        if not strategy.validate_config():
            self.logger.error(f"Invalid config for strategy: {strategy.config.name}")
            return False
        
        strategy_name = strategy.config.name
        self._strategies[strategy_name] = strategy
        self._strategy_configs[strategy_name] = strategy.config
        
        self.logger.info(f"Registered strategy: {strategy_name}")
        return True
    
    def unregister_strategy(self, strategy_name: str) -> bool:
        """
        Hủy đăng ký strategy
        
        Args:
            strategy_name: Tên strategy
            
        Returns:
            bool: True nếu hủy đăng ký thành công
        """
        if strategy_name in self._strategies:
            del self._strategies[strategy_name]
            del self._strategy_configs[strategy_name]
            self.logger.info(f"Unregistered strategy: {strategy_name}")
            return True
        return False
    
    def get_strategy(self, strategy_name: str) -> Optional[BaseStrategy]:
        """
        Lấy strategy theo tên
        
        Args:
            strategy_name: Tên strategy
            
        Returns:
            Optional[BaseStrategy]: Strategy instance hoặc None
        """
        return self._strategies.get(strategy_name)
    
    def get_active_strategies(self) -> List[BaseStrategy]:
        """
        Lấy danh sách strategies đang active
        
        Returns:
            List[BaseStrategy]: Danh sách active strategies
        """
        return [strategy for strategy in self._strategies.values() 
                if strategy.config.is_active]
    
    def get_strategy_names(self) -> List[str]:
        """
        Lấy danh sách tên strategies
        
        Returns:
            List[str]: Danh sách tên strategies
        """
        return list(self._strategies.keys())
    
    def get_strategy_info(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin strategy
        
        Args:
            strategy_name: Tên strategy
            
        Returns:
            Optional[Dict[str, Any]]: Thông tin strategy hoặc None
        """
        strategy = self.get_strategy(strategy_name)
        return strategy.get_strategy_info() if strategy else None
    
    def get_all_strategy_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Lấy thông tin tất cả strategies
        
        Returns:
            Dict[str, Dict[str, Any]]: Thông tin tất cả strategies
        """
        return {name: strategy.get_strategy_info() 
                for name, strategy in self._strategies.items()}

# Global strategy registry
strategy_registry = StrategyRegistry()
