"""
Worker Factory for Creating Workers with Dependency Injection

This module provides a factory for creating workers with proper
dependency injection and configuration.
"""

from typing import Dict, Any, Optional
from .service_container import ServiceContainer, ServiceConfig
from ..base_worker import BaseRQWorker
from ..strategies.base_strategy import MarketData, Signal
from ..pipeline.base_pipeline import ProcessingResult
from app.services.debug import debug_helper


class EnhancedWorker(BaseRQWorker):
    """
    Enhanced worker using dependency injection and design patterns.
    
    This worker uses the service container to get its dependencies
    and implements the new strategy and pipeline patterns.
    """
    
    def __init__(self, container: ServiceContainer, worker_name: Optional[str] = None):
        """
        Initialize enhanced worker.
        
        Args:
            container: Service container with dependencies
            worker_name: Optional worker name
        """
        super().__init__()
        
        self.container = container
        self.worker_name = worker_name or f"Enhanced_{container.config.market}_{container.config.worker_type}"
        
        # Get dependencies from container
        self.market_data_repository = container.get('market_data_repository')
        self.signal_notifier = container.get('signal_notifier')
        self.pipeline = container.get('processing_pipeline')
        self.strategies = container.get_worker_config()['strategies']
        
        debug_helper.log_step(f"Initialized enhanced worker: {self.worker_name}")
    
    def get_listen_queues(self) -> list[str]:
        """Get list of queues to listen to."""
        market = self.container.config.market.lower()
        return [market]
    
    def process_symbol(self, symbol: str, exchange: str, timeframe: str = "1h") -> Optional[Signal]:
        """
        Process a symbol using the enhanced pipeline.
        
        Args:
            symbol: Symbol ticker
            exchange: Exchange name
            timeframe: Timeframe
            
        Returns:
            Generated signal or None
        """
        try:
            debug_helper.log_step(f"Processing {symbol} with enhanced worker")
            
            # Get market data
            candles = self.market_data_repository.get_candles(symbol, timeframe, limit=1000)
            
            if candles.empty:
                debug_helper.log_step(f"No data available for {symbol}")
                return None
            
            # Create market data object
            market_data = MarketData(
                symbol=symbol,
                exchange=exchange,
                timeframe=timeframe,
                candles=candles,
                timestamp=candles.index[-1] if not candles.empty else None
            )
            
            # Execute pipeline
            result = self.pipeline.execute(market_data)
            
            if not result.success:
                debug_helper.log_step(f"Pipeline failed for {symbol}: {result.error}")
                return None
            
            # Get generated signals
            signals = result.signals or []
            
            if signals:
                # Notify observers about signals
                for signal in signals:
                    self.signal_notifier.notify_signal(signal)
                
                # Return the first signal (or could return all)
                return signals[0]
            else:
                debug_helper.log_step(f"No signals generated for {symbol}")
                return None
                
        except Exception as e:
            debug_helper.log_step(f"Error processing {symbol} with enhanced worker", error=e)
            return None


class WorkerFactory:
    """
    Factory for creating workers with dependency injection.
    
    This factory creates workers with proper configuration and
    dependency injection using the service container.
    """
    
    @staticmethod
    def create_worker(worker_type: str, 
                     market: str, 
                     config: Optional[Dict[str, Any]] = None) -> EnhancedWorker:
        """
        Create a worker with dependency injection.
        
        Args:
            worker_type: Type of worker ("macd", "sma", "hybrid")
            market: Market type ("US", "VN")
            config: Optional configuration overrides
            
        Returns:
            Configured worker instance
        """
        try:
            # Create service configuration
            service_config = ServiceConfig(
                market=market,
                worker_type=worker_type
            )
            
            # Apply configuration overrides
            if config:
                for key, value in config.items():
                    if hasattr(service_config, key):
                        setattr(service_config, key, value)
            
            # Create service container
            container = ServiceContainer(service_config)
            container.initialize_default_services()
            
            # Create worker
            worker = EnhancedWorker(container)
            
            debug_helper.log_step(f"Created {worker_type} worker for {market} market")
            return worker
            
        except Exception as e:
            debug_helper.log_step(f"Error creating {worker_type} worker for {market} market", error=e)
            raise
    
    @staticmethod
    def create_us_macd_worker(config: Optional[Dict[str, Any]] = None) -> EnhancedWorker:
        """
        Create US MACD worker.
        
        Args:
            config: Optional configuration overrides
            
        Returns:
            US MACD worker instance
        """
        return WorkerFactory.create_worker("macd", "US", config)
    
    @staticmethod
    def create_vn_macd_worker(config: Optional[Dict[str, Any]] = None) -> EnhancedWorker:
        """
        Create VN MACD worker.
        
        Args:
            config: Optional configuration overrides
            
        Returns:
            VN MACD worker instance
        """
        return WorkerFactory.create_worker("macd", "VN", config)
    
    @staticmethod
    def create_us_sma_worker(config: Optional[Dict[str, Any]] = None) -> EnhancedWorker:
        """
        Create US SMA worker.
        
        Args:
            config: Optional configuration overrides
            
        Returns:
            US SMA worker instance
        """
        return WorkerFactory.create_worker("sma", "US", config)
    
    @staticmethod
    def create_vn_sma_worker(config: Optional[Dict[str, Any]] = None) -> EnhancedWorker:
        """
        Create VN SMA worker.
        
        Args:
            config: Optional configuration overrides
            
        Returns:
            VN SMA worker instance
        """
        return WorkerFactory.create_worker("sma", "VN", config)
    
    @staticmethod
    def create_hybrid_worker(market: str, config: Optional[Dict[str, Any]] = None) -> EnhancedWorker:
        """
        Create hybrid worker (MACD + SMA).
        
        Args:
            market: Market type ("US", "VN")
            config: Optional configuration overrides
            
        Returns:
            Hybrid worker instance
        """
        return WorkerFactory.create_worker("hybrid", market, config)
    
    @staticmethod
    def get_worker_config_template() -> Dict[str, Any]:
        """
        Get worker configuration template.
        
        Returns:
            Configuration template dictionary
        """
        return {
            # Database configuration
            'database_url': 'mysql+pymysql://user:password@localhost:3306/database',
            
            # Redis configuration
            'redis_url': 'redis://localhost:6379/0',
            
            # Telegram configuration
            'telegram_bot_token': 'your_bot_token',
            'telegram_chat_id': 'your_chat_id',
            
            # API configuration
            'api_key': 'your_api_key',
            
            # Strategy configuration
            'macd_fast_period': 7,
            'macd_slow_period': 72,
            'macd_signal_period': 144,
            
            'sma_m1_period': 18,
            'sma_m2_period': 36,
            'sma_m3_period': 48,
            'sma_ma144_period': 144,
            
            # Pipeline configuration
            'min_candles': 50,
            'indicator_types': ['macd', 'sma'],
            
            # Observer configuration
            'enable_telegram': True,
            'enable_database': True,
            'enable_websocket': True
        }
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate worker configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            Validated configuration
            
        Raises:
            ValueError: If configuration is invalid
        """
        validated_config = config.copy()
        
        # Validate required fields
        required_fields = ['market', 'worker_type']
        for field in required_fields:
            if field not in validated_config:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate market
        if validated_config['market'] not in ['US', 'VN']:
            raise ValueError("Market must be 'US' or 'VN'")
        
        # Validate worker type
        if validated_config['worker_type'] not in ['macd', 'sma', 'hybrid']:
            raise ValueError("Worker type must be 'macd', 'sma', or 'hybrid'")
        
        # Validate numeric fields
        numeric_fields = [
            'macd_fast_period', 'macd_slow_period', 'macd_signal_period',
            'sma_m1_period', 'sma_m2_period', 'sma_m3_period', 'sma_ma144_period',
            'min_candles'
        ]
        
        for field in numeric_fields:
            if field in validated_config:
                if not isinstance(validated_config[field], (int, float)) or validated_config[field] <= 0:
                    raise ValueError(f"{field} must be a positive number")
        
        # Validate boolean fields
        boolean_fields = ['enable_telegram', 'enable_database', 'enable_websocket']
        for field in boolean_fields:
            if field in validated_config:
                if not isinstance(validated_config[field], bool):
                    raise ValueError(f"{field} must be a boolean")
        
        return validated_config
