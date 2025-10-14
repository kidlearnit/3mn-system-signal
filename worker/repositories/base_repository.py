"""
Base Repository Classes

This module defines the abstract base classes for the Repository pattern
used in data access layer.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

from ..strategies.base_strategy import MarketData, Signal


@dataclass
class RepositoryConfig:
    """Configuration for repository implementations"""
    
    connection_string: Optional[str] = None
    api_key: Optional[str] = None
    timeout: int = 30
    retry_count: int = 3
    cache_ttl: int = 300  # 5 minutes
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseRepository(ABC):
    """
    Abstract base class for all repository implementations.
    
    This class defines the common interface and functionality
    for data access operations.
    """
    
    def __init__(self, config: RepositoryConfig):
        """
        Initialize the repository.
        
        Args:
            config: Repository configuration
        """
        self.config = config
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the repository is available and accessible.
        
        Returns:
            True if repository is available, False otherwise
        """
        pass
    
    def get_cache_key(self, operation: str, **kwargs) -> str:
        """
        Generate cache key for an operation.
        
        Args:
            operation: Operation name
            **kwargs: Operation parameters
            
        Returns:
            Cache key string
        """
        key_parts = [operation]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        return "|".join(key_parts)
    
    def is_cache_valid(self, key: str) -> bool:
        """
        Check if cached data is still valid.
        
        Args:
            key: Cache key
            
        Returns:
            True if cache is valid, False otherwise
        """
        if key not in self._cache or key not in self._cache_timestamps:
            return False
        
        cache_time = self._cache_timestamps[key]
        age = (datetime.now() - cache_time).total_seconds()
        return age < self.config.cache_ttl
    
    def get_from_cache(self, key: str) -> Optional[Any]:
        """
        Get data from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if not found/invalid
        """
        if self.is_cache_valid(key):
            return self._cache[key]
        return None
    
    def set_cache(self, key: str, data: Any) -> None:
        """
        Set data in cache.
        
        Args:
            key: Cache key
            data: Data to cache
        """
        self._cache[key] = data
        self._cache_timestamps[key] = datetime.now()
    
    def clear_cache(self, key: Optional[str] = None) -> None:
        """
        Clear cache.
        
        Args:
            key: Specific cache key to clear, or None to clear all
        """
        if key:
            self._cache.pop(key, None)
            self._cache_timestamps.pop(key, None)
        else:
            self._cache.clear()
            self._cache_timestamps.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'total_entries': len(self._cache),
            'valid_entries': sum(1 for key in self._cache.keys() if self.is_cache_valid(key)),
            'cache_ttl': self.config.cache_ttl,
            'oldest_entry': min(self._cache_timestamps.values()) if self._cache_timestamps else None,
            'newest_entry': max(self._cache_timestamps.values()) if self._cache_timestamps else None
        }


class MarketDataRepository(BaseRepository):
    """
    Abstract base class for market data repositories.
    
    This class defines the interface for accessing market data
    from various sources (database, API, etc.).
    """
    
    @abstractmethod
    def get_candles(self, 
                   symbol: str, 
                   timeframe: str, 
                   limit: int = 1000,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Get candle data for a symbol and timeframe.
        
        Args:
            symbol: Symbol ticker
            timeframe: Timeframe (e.g., '1m', '5m', '1h')
            limit: Maximum number of candles to return
            start_date: Start date for data range
            end_date: End date for data range
            
        Returns:
            DataFrame with OHLCV data
            
        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If data retrieval fails
        """
        pass
    
    @abstractmethod
    def get_latest_candles(self, 
                          symbol: str, 
                          timeframe: str, 
                          count: int = 1) -> pd.DataFrame:
        """
        Get latest candle data for a symbol and timeframe.
        
        Args:
            symbol: Symbol ticker
            timeframe: Timeframe
            count: Number of latest candles to return
            
        Returns:
            DataFrame with latest OHLCV data
        """
        pass
    
    @abstractmethod
    def save_candles(self, 
                    symbol: str, 
                    timeframe: str, 
                    candles: pd.DataFrame) -> bool:
        """
        Save candle data for a symbol and timeframe.
        
        Args:
            symbol: Symbol ticker
            timeframe: Timeframe
            candles: DataFrame with OHLCV data
            
        Returns:
            True if save was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get symbol information.
        
        Args:
            symbol: Symbol ticker
            
        Returns:
            Dictionary with symbol information or None if not found
        """
        pass
    
    @abstractmethod
    def get_active_symbols(self) -> List[Dict[str, Any]]:
        """
        Get list of active symbols.
        
        Returns:
            List of dictionaries with symbol information
        """
        pass


class SignalRepository(BaseRepository):
    """
    Abstract base class for signal repositories.
    
    This class defines the interface for accessing and storing
    trading signals.
    """
    
    @abstractmethod
    def save_signal(self, signal: Signal) -> bool:
        """
        Save a trading signal.
        
        Args:
            signal: Signal object to save
            
        Returns:
            True if save was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_signals(self, 
                   symbol: Optional[str] = None,
                   signal_type: Optional[str] = None,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   limit: int = 100) -> List[Signal]:
        """
        Get trading signals with optional filters.
        
        Args:
            symbol: Filter by symbol
            signal_type: Filter by signal type ('BUY', 'SELL', 'HOLD')
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of signals to return
            
        Returns:
            List of Signal objects
        """
        pass
    
    @abstractmethod
    def get_latest_signal(self, symbol: str) -> Optional[Signal]:
        """
        Get the latest signal for a symbol.
        
        Args:
            symbol: Symbol ticker
            
        Returns:
            Latest Signal object or None if not found
        """
        pass
    
    @abstractmethod
    def delete_old_signals(self, days: int = 30) -> int:
        """
        Delete old signals.
        
        Args:
            days: Delete signals older than this many days
            
        Returns:
            Number of signals deleted
        """
        pass


class WorkflowRepository(BaseRepository):
    """
    Abstract base class for workflow repositories.
    
    This class defines the interface for accessing workflow
    configurations and data.
    """
    
    @abstractmethod
    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """
        Get list of active workflows.
        
        Returns:
            List of workflow dictionaries
        """
        pass
    
    @abstractmethod
    def get_workflow_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get workflow by name.
        
        Args:
            name: Workflow name
            
        Returns:
            Workflow dictionary or None if not found
        """
        pass
    
    @abstractmethod
    def get_macd_config_for_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get MACD configuration for a symbol from workflows.
        
        Args:
            symbol: Symbol ticker
            
        Returns:
            MACD configuration dictionary or None if not found
        """
        pass
    
    @abstractmethod
    def update_workflow(self, workflow_id: int, data: Dict[str, Any]) -> bool:
        """
        Update workflow data.
        
        Args:
            workflow_id: Workflow ID
            data: Data to update
            
        Returns:
            True if update was successful, False otherwise
        """
        pass
