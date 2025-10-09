"""
Database Observer Implementation

This module implements the database observer for logging trading signals
to the database.
"""

from typing import Optional, Dict, Any
from datetime import datetime

from .base_observer import SignalObserver, SignalEvent
from ..repositories.signal_repository import DatabaseSignalRepository, RepositoryConfig
from app.services.debug import debug_helper


class DatabaseObserver(SignalObserver):
    """
    Database observer for logging trading signals to the database.
    
    This observer saves trading signals to the database for historical
    tracking and analysis.
    """
    
    def __init__(self, 
                 repository: Optional[DatabaseSignalRepository] = None,
                 name: Optional[str] = None):
        """
        Initialize database observer.
        
        Args:
            repository: Signal repository instance
            name: Optional observer name
        """
        super().__init__(name)
        
        self.repository = repository
        if self.repository is None:
            # Create default repository
            config = RepositoryConfig(connection_string=None)  # Will use default connection
            self.repository = DatabaseSignalRepository(config)
    
    def handle_signal(self, event: SignalEvent) -> bool:
        """
        Handle a signal event by saving it to the database.
        
        Args:
            event: Signal event to handle
            
        Returns:
            True if signal was saved successfully, False otherwise
        """
        try:
            if not self.repository.is_available():
                debug_helper.log_step("Database observer: repository not available")
                return False
            
            # Save signal to database
            success = self.repository.save_signal(event.signal)
            
            if success:
                debug_helper.log_step(
                    f"Saved signal to database: {event.signal.symbol} - {event.signal.signal_type}"
                )
            else:
                debug_helper.log_step(
                    f"Failed to save signal to database: {event.signal.symbol}"
                )
            
            return success
            
        except Exception as e:
            debug_helper.log_step(f"Error handling database signal for {event.signal.symbol}", error=e)
            return False
    
    def set_repository(self, repository: DatabaseSignalRepository) -> None:
        """
        Set the signal repository.
        
        Args:
            repository: Signal repository instance
        """
        self.repository = repository
    
    def get_repository(self) -> DatabaseSignalRepository:
        """
        Get the signal repository.
        
        Returns:
            Signal repository instance
        """
        return self.repository


class DatabaseLogObserver(SignalObserver):
    """
    Database observer for general logging.
    
    This observer logs various types of events to the database,
    not just trading signals.
    """
    
    def __init__(self, 
                 repository: Optional[DatabaseSignalRepository] = None,
                 log_level: str = "INFO",
                 name: Optional[str] = None):
        """
        Initialize database log observer.
        
        Args:
            repository: Signal repository instance
            log_level: Log level filter
            name: Optional observer name
        """
        super().__init__(name)
        
        self.repository = repository
        self.log_level = log_level
        
        if self.repository is None:
            # Create default repository
            config = RepositoryConfig(connection_string=None)
            self.repository = DatabaseSignalRepository(config)
    
    def handle_signal(self, event: SignalEvent) -> bool:
        """
        Handle a signal event by logging it.
        
        Args:
            event: Signal event to handle
            
        Returns:
            True if event was logged successfully, False otherwise
        """
        try:
            # Log the event (this could be extended to use a proper logging table)
            debug_helper.log_step(
                f"Database log: {event.event_type} for {event.signal.symbol}",
                {
                    'signal_type': event.signal.signal_type,
                    'confidence': event.signal.confidence,
                    'strength': event.signal.strength,
                    'timestamp': event.timestamp.isoformat(),
                    'metadata': event.metadata
                }
            )
            
            return True
            
        except Exception as e:
            debug_helper.log_step(f"Error logging database event for {event.signal.symbol}", error=e)
            return False
    
    def set_log_level(self, log_level: str) -> None:
        """
        Set the log level filter.
        
        Args:
            log_level: Log level ("DEBUG", "INFO", "WARNING", "ERROR")
        """
        self.log_level = log_level


class DatabaseAnalyticsObserver(SignalObserver):
    """
    Database observer for analytics and statistics.
    
    This observer tracks signal statistics and performance metrics
    in the database.
    """
    
    def __init__(self, 
                 repository: Optional[DatabaseSignalRepository] = None,
                 name: Optional[str] = None):
        """
        Initialize database analytics observer.
        
        Args:
            repository: Signal repository instance
            name: Optional observer name
        """
        super().__init__(name)
        
        self.repository = repository
        self._stats = {
            'total_signals': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'hold_signals': 0,
            'high_confidence_signals': 0,
            'symbols_tracked': set(),
            'strategies_used': set()
        }
        
        if self.repository is None:
            # Create default repository
            config = RepositoryConfig(connection_string=None)
            self.repository = DatabaseSignalRepository(config)
    
    def handle_signal(self, event: SignalEvent) -> bool:
        """
        Handle a signal event by updating analytics.
        
        Args:
            event: Signal event to handle
            
        Returns:
            True if analytics were updated successfully, False otherwise
        """
        try:
            signal = event.signal
            
            # Update statistics
            self._stats['total_signals'] += 1
            self._stats['symbols_tracked'].add(signal.symbol)
            self._stats['strategies_used'].add(signal.strategy_name)
            
            if signal.signal_type == 'BUY':
                self._stats['buy_signals'] += 1
            elif signal.signal_type == 'SELL':
                self._stats['sell_signals'] += 1
            else:
                self._stats['hold_signals'] += 1
            
            if signal.confidence >= 0.8:
                self._stats['high_confidence_signals'] += 1
            
            # Log analytics update
            debug_helper.log_step(
                f"Updated analytics for {signal.symbol}",
                {
                    'signal_type': signal.signal_type,
                    'confidence': signal.confidence,
                    'total_signals': self._stats['total_signals'],
                    'symbols_count': len(self._stats['symbols_tracked']),
                    'strategies_count': len(self._stats['strategies_used'])
                }
            )
            
            return True
            
        except Exception as e:
            debug_helper.log_step(f"Error updating analytics for {event.signal.symbol}", error=e)
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current analytics statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'total_signals': self._stats['total_signals'],
            'buy_signals': self._stats['buy_signals'],
            'sell_signals': self._stats['sell_signals'],
            'hold_signals': self._stats['hold_signals'],
            'high_confidence_signals': self._stats['high_confidence_signals'],
            'symbols_tracked': len(self._stats['symbols_tracked']),
            'strategies_used': len(self._stats['strategies_used']),
            'symbols_list': list(self._stats['symbols_tracked']),
            'strategies_list': list(self._stats['strategies_used'])
        }
    
    def reset_stats(self) -> None:
        """Reset analytics statistics."""
        self._stats = {
            'total_signals': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'hold_signals': 0,
            'high_confidence_signals': 0,
            'symbols_tracked': set(),
            'strategies_used': set()
        }
