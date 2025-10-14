"""
Service Container for Dependency Injection

This module provides a service container for managing dependencies
and configurations using dependency injection pattern.
"""

import os
from typing import Dict, Any, Optional, Type, TypeVar, Callable
from dataclasses import dataclass
from datetime import datetime

from ..repositories.base_repository import RepositoryConfig
from ..repositories.market_data_repository import DatabaseMarketDataRepository, APIMarketDataRepository
from ..repositories.signal_repository import DatabaseSignalRepository
from ..repositories.workflow_repository import DatabaseWorkflowRepository
from ..observers.base_observer import SignalNotifier
from ..observers.telegram_observer import TelegramObserver, TelegramMarketObserver
from ..observers.database_observer import DatabaseObserver, DatabaseAnalyticsObserver
from ..observers.websocket_observer import WebSocketObserver, WebSocketMarketObserver
from ..strategies.macd_strategy import MACDStrategy, MACDThresholdStrategy
from ..strategies.sma_strategy import SMAStrategy, MultiTimeframeSMAStrategy
from ..pipeline.base_pipeline import ProcessingPipeline
from ..pipeline.data_validation_step import DataValidationStep
from ..pipeline.indicator_calculation_step import IndicatorCalculationStep
from ..pipeline.signal_evaluation_step import SignalEvaluationStep
from ..pipeline.data_fetch_step import DataFetchStep

T = TypeVar('T')


@dataclass
class ServiceConfig:
    """Configuration for service container"""
    
    # Database configuration
    database_url: Optional[str] = None
    
    # Redis configuration
    redis_url: Optional[str] = None
    
    # Telegram configuration
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    
    # API configuration
    api_key: Optional[str] = None
    
    # Worker configuration
    market: str = "US"
    worker_type: str = "macd"
    
    # Strategy configuration
    macd_fast_period: int = 7
    macd_slow_period: int = 72
    macd_signal_period: int = 144
    
    sma_m1_period: int = 18
    sma_m2_period: int = 36
    sma_m3_period: int = 48
    sma_ma144_period: int = 144
    
    # Pipeline configuration
    min_candles: int = 50
    indicator_types: list = None
    
    # Observer configuration
    enable_telegram: bool = True
    enable_database: bool = True
    enable_websocket: bool = True
    
    def __post_init__(self):
        # Set defaults from environment variables
        if self.database_url is None:
            self.database_url = os.getenv('DATABASE_URL')
        
        if self.redis_url is None:
            self.redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
        
        if self.telegram_bot_token is None:
            self.telegram_bot_token = os.getenv('TG_TOKEN')
        
        if self.telegram_chat_id is None:
            self.telegram_chat_id = os.getenv('TG_CHAT_ID')
        
        if self.api_key is None:
            self.api_key = os.getenv('API_KEY')
        
        if self.indicator_types is None:
            self.indicator_types = ['macd', 'sma']


class ServiceContainer:
    """
    Service container for dependency injection.
    
    This container manages service instances and their dependencies,
    providing a centralized way to configure and access services.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        """
        Initialize service container.
        
        Args:
            config: Service configuration
        """
        self.config = config or ServiceConfig()
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._initialized = False
    
    def register_singleton(self, name: str, service: Any) -> None:
        """
        Register a singleton service instance.
        
        Args:
            name: Service name
            service: Service instance
        """
        self._singletons[name] = service
    
    def register_factory(self, name: str, factory: Callable) -> None:
        """
        Register a service factory.
        
        Args:
            name: Service name
            factory: Factory function
        """
        self._factories[name] = factory
    
    def get(self, name: str) -> Any:
        """
        Get a service by name.
        
        Args:
            name: Service name
            
        Returns:
            Service instance
            
        Raises:
            KeyError: If service is not registered
        """
        # Check singletons first
        if name in self._singletons:
            return self._singletons[name]
        
        # Check factories
        if name in self._factories:
            service = self._factories[name]()
            self._singletons[name] = service  # Cache as singleton
            return service
        
        # Check if service exists in _services
        if name in self._services:
            return self._services[name]
        
        raise KeyError(f"Service '{name}' not registered")
    
    def get_or_create(self, name: str, factory: Callable) -> Any:
        """
        Get a service or create it if it doesn't exist.
        
        Args:
            name: Service name
            factory: Factory function
            
        Returns:
            Service instance
        """
        try:
            return self.get(name)
        except KeyError:
            service = factory()
            self.register_singleton(name, service)
            return service
    
    def initialize_default_services(self) -> None:
        """Initialize default services."""
        if self._initialized:
            return
        
        # Repository configurations
        db_config = RepositoryConfig(connection_string=self.config.database_url)
        api_config = RepositoryConfig(api_key=self.config.api_key)
        
        # Register repositories
        self.register_factory('market_data_repository', 
                             lambda: DatabaseMarketDataRepository(db_config))
        self.register_factory('api_market_data_repository',
                             lambda: APIMarketDataRepository(api_config))
        self.register_factory('signal_repository',
                             lambda: DatabaseSignalRepository(db_config))
        self.register_factory('workflow_repository',
                             lambda: DatabaseWorkflowRepository(db_config))
        
        # Register strategies
        self.register_factory('macd_strategy',
                             lambda: MACDStrategy(
                                 fast_period=self.config.macd_fast_period,
                                 slow_period=self.config.macd_slow_period,
                                 signal_period=self.config.macd_signal_period
                             ))
        self.register_factory('macd_threshold_strategy',
                             lambda: MACDThresholdStrategy(
                                 fast_period=self.config.macd_fast_period,
                                 slow_period=self.config.macd_slow_period,
                                 signal_period=self.config.macd_signal_period
                             ))
        self.register_factory('sma_strategy',
                             lambda: SMAStrategy(
                                 m1_period=self.config.sma_m1_period,
                                 m2_period=self.config.sma_m2_period,
                                 m3_period=self.config.sma_m3_period,
                                 ma144_period=self.config.sma_ma144_period
                             ))
        self.register_factory('multi_timeframe_sma_strategy',
                             lambda: MultiTimeframeSMAStrategy(
                                 m1_period=self.config.sma_m1_period,
                                 m2_period=self.config.sma_m2_period,
                                 m3_period=self.config.sma_m3_period,
                                 ma144_period=self.config.sma_ma144_period
                             ))
        
        # Register pipeline steps
        self.register_factory('data_validation_step',
                             lambda: DataValidationStep(min_candles=self.config.min_candles))
        self.register_factory('indicator_calculation_step',
                             lambda: IndicatorCalculationStep(indicator_types=self.config.indicator_types))
        self.register_factory('data_fetch_step',
                             lambda: DataFetchStep())
        
        # Register signal evaluation step with strategies
        def create_signal_evaluation_step():
            strategies = [
                self.get('macd_strategy'),
                self.get('sma_strategy')
            ]
            return SignalEvaluationStep(strategies=strategies)
        
        self.register_factory('signal_evaluation_step', create_signal_evaluation_step)
        
        # Register processing pipeline
        def create_processing_pipeline():
            pipeline = ProcessingPipeline(f"Worker_{self.config.market}_{self.config.worker_type}")
            pipeline.add_step(self.get('data_validation_step'))
            pipeline.add_step(self.get('indicator_calculation_step'))
            pipeline.add_step(self.get('signal_evaluation_step'))
            return pipeline
        
        self.register_factory('processing_pipeline', create_processing_pipeline)
        
        # Register observers
        if self.config.enable_telegram and self.config.telegram_bot_token:
            self.register_factory('telegram_observer',
                                 lambda: TelegramMarketObserver(
                                     bot_token=self.config.telegram_bot_token,
                                     chat_id=self.config.telegram_chat_id,
                                     market=self.config.market
                                 ))
        
        if self.config.enable_database:
            def create_database_observer():
                return DatabaseObserver(repository=self.get('signal_repository'))
            
            self.register_factory('database_observer', create_database_observer)
            
            def create_analytics_observer():
                return DatabaseAnalyticsObserver(repository=self.get('signal_repository'))
            
            self.register_factory('analytics_observer', create_analytics_observer)
        
        if self.config.enable_websocket:
            self.register_factory('websocket_observer',
                                 lambda: WebSocketMarketObserver(
                                     redis_url=self.config.redis_url,
                                     market=self.config.market
                                 ))
        
        # Register signal notifier
        def create_signal_notifier():
            notifier = SignalNotifier()
            
            # Add observers
            if self.config.enable_telegram and self.config.telegram_bot_token:
                try:
                    notifier.subscribe(self.get('telegram_observer'))
                except KeyError:
                    pass  # Telegram not configured
            
            if self.config.enable_database:
                try:
                    notifier.subscribe(self.get('database_observer'))
                    notifier.subscribe(self.get('analytics_observer'))
                except KeyError:
                    pass  # Database not configured
            
            if self.config.enable_websocket:
                try:
                    notifier.subscribe(self.get('websocket_observer'))
                except KeyError:
                    pass  # WebSocket not configured
            
            return notifier
        
        self.register_factory('signal_notifier', create_signal_notifier)
        
        self._initialized = True
    
    def get_worker_config(self) -> Dict[str, Any]:
        """
        Get worker configuration.
        
        Returns:
            Dictionary with worker configuration
        """
        return {
            'market_data_repository': self.get('market_data_repository'),
            'signal_notifier': self.get('signal_notifier'),
            'pipeline': self.get('processing_pipeline'),
            'strategies': [
                self.get('macd_strategy'),
                self.get('sma_strategy')
            ]
        }
    
    def get_available_services(self) -> Dict[str, str]:
        """
        Get list of available services.
        
        Returns:
            Dictionary mapping service names to their types
        """
        services = {}
        
        # Add singletons
        for name, service in self._singletons.items():
            services[name] = type(service).__name__
        
        # Add factories
        for name, factory in self._factories.items():
            services[name] = f"Factory({factory.__name__})"
        
        return services
    
    def get_service_stats(self) -> Dict[str, Any]:
        """
        Get service container statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'total_services': len(self._services),
            'singletons': len(self._singletons),
            'factories': len(self._factories),
            'initialized': self._initialized,
            'config': {
                'market': self.config.market,
                'worker_type': self.config.worker_type,
                'enable_telegram': self.config.enable_telegram,
                'enable_database': self.config.enable_database,
                'enable_websocket': self.config.enable_websocket
            }
        }
    
    def clear_services(self) -> None:
        """Clear all services."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        self._initialized = False
    
    def __str__(self) -> str:
        """String representation of the container"""
        return f"ServiceContainer({len(self._services)} services, {len(self._singletons)} singletons)"
    
    def __repr__(self) -> str:
        """Detailed string representation of the container"""
        return f"ServiceContainer(services={len(self._services)}, singletons={len(self._singletons)}, initialized={self._initialized})"
