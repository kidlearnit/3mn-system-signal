"""
Base Observer Classes

This module defines the abstract base classes for the Observer pattern
used in event handling and notifications.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import threading

from ..strategies.base_strategy import Signal


@dataclass
class SignalEvent:
    """Container for signal events"""
    
    signal: Signal
    event_type: str  # 'new_signal', 'signal_update', 'signal_expired'
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SignalObserver(ABC):
    """
    Abstract base class for signal observers.
    
    Observers are notified when signal events occur and can perform
    actions like sending notifications, logging, or updating databases.
    """
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize the observer.
        
        Args:
            name: Optional name for the observer
        """
        self.name = name or self.__class__.__name__
        self._enabled = True
        self._filters: Dict[str, Any] = {}
    
    @abstractmethod
    def handle_signal(self, event: SignalEvent) -> bool:
        """
        Handle a signal event.
        
        Args:
            event: Signal event to handle
            
        Returns:
            True if event was handled successfully, False otherwise
        """
        pass
    
    def get_name(self) -> str:
        """
        Get observer name.
        
        Returns:
            Observer name
        """
        return self.name
    
    def is_enabled(self) -> bool:
        """
        Check if observer is enabled.
        
        Returns:
            True if enabled, False otherwise
        """
        return self._enabled
    
    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the observer.
        
        Args:
            enabled: True to enable, False to disable
        """
        self._enabled = enabled
    
    def add_filter(self, key: str, value: Any) -> None:
        """
        Add a filter to the observer.
        
        Args:
            key: Filter key
            value: Filter value
        """
        self._filters[key] = value
    
    def remove_filter(self, key: str) -> None:
        """
        Remove a filter from the observer.
        
        Args:
            key: Filter key to remove
        """
        self._filters.pop(key, None)
    
    def get_filters(self) -> Dict[str, Any]:
        """
        Get observer filters.
        
        Returns:
            Dictionary of filters
        """
        return self._filters.copy()
    
    def should_handle_event(self, event: SignalEvent) -> bool:
        """
        Check if observer should handle the event based on filters.
        
        Args:
            event: Signal event to check
            
        Returns:
            True if event should be handled, False otherwise
        """
        if not self._enabled:
            return False
        
        # Apply filters
        for key, value in self._filters.items():
            if key == 'symbols' and event.signal.symbol not in value:
                return False
            elif key == 'signal_types' and event.signal.signal_type not in value:
                return False
            elif key == 'min_confidence' and event.signal.confidence < value:
                return False
            elif key == 'min_strength' and event.signal.strength < value:
                return False
            elif key == 'timeframes' and event.signal.timeframe not in value:
                return False
        
        return True
    
    def __str__(self) -> str:
        """String representation of the observer"""
        return f"{self.name}(enabled={self._enabled}, filters={len(self._filters)})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the observer"""
        return f"{self.__class__.__name__}(name='{self.name}', enabled={self._enabled})"


class SignalNotifier:
    """
    Main signal notification system using the Observer pattern.
    
    This class manages observers and notifies them when signal events occur.
    """
    
    def __init__(self):
        """Initialize the signal notifier."""
        self.observers: List[SignalObserver] = []
        self._lock = threading.Lock()
        self._event_history: List[SignalEvent] = []
        self._max_history = 1000
    
    def subscribe(self, observer: SignalObserver) -> bool:
        """
        Subscribe an observer to signal events.
        
        Args:
            observer: Observer to subscribe
            
        Returns:
            True if subscription was successful, False otherwise
        """
        try:
            with self._lock:
                if observer not in self.observers:
                    self.observers.append(observer)
                    return True
                else:
                    return False
        except Exception:
            return False
    
    def unsubscribe(self, observer: SignalObserver) -> bool:
        """
        Unsubscribe an observer from signal events.
        
        Args:
            observer: Observer to unsubscribe
            
        Returns:
            True if unsubscription was successful, False otherwise
        """
        try:
            with self._lock:
                if observer in self.observers:
                    self.observers.remove(observer)
                    return True
                else:
                    return False
        except Exception:
            return False
    
    def notify(self, event: SignalEvent) -> Dict[str, bool]:
        """
        Notify all observers about a signal event.
        
        Args:
            event: Signal event to notify about
            
        Returns:
            Dictionary mapping observer names to success status
        """
        results = {}
        
        with self._lock:
            # Add to event history
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
            
            # Notify observers
            for observer in self.observers:
                try:
                    if observer.should_handle_event(event):
                        success = observer.handle_signal(event)
                        results[observer.get_name()] = success
                    else:
                        results[observer.get_name()] = False  # Filtered out
                except Exception as e:
                    results[observer.get_name()] = False
                    # Log error but continue with other observers
        
        return results
    
    def notify_signal(self, signal: Signal, event_type: str = 'new_signal', metadata: Optional[Dict[str, Any]] = None) -> Dict[str, bool]:
        """
        Convenience method to notify about a signal.
        
        Args:
            signal: Signal to notify about
            event_type: Type of event
            metadata: Optional metadata
            
        Returns:
            Dictionary mapping observer names to success status
        """
        event = SignalEvent(
            signal=signal,
            event_type=event_type,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        return self.notify(event)
    
    def get_observers(self) -> List[SignalObserver]:
        """
        Get list of subscribed observers.
        
        Returns:
            List of observers
        """
        with self._lock:
            return self.observers.copy()
    
    def get_observer_count(self) -> int:
        """
        Get number of subscribed observers.
        
        Returns:
            Number of observers
        """
        with self._lock:
            return len(self.observers)
    
    def get_enabled_observers(self) -> List[SignalObserver]:
        """
        Get list of enabled observers.
        
        Returns:
            List of enabled observers
        """
        with self._lock:
            return [obs for obs in self.observers if obs.is_enabled()]
    
    def clear_observers(self) -> None:
        """Clear all observers."""
        with self._lock:
            self.observers.clear()
    
    def get_event_history(self, limit: Optional[int] = None) -> List[SignalEvent]:
        """
        Get event history.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of recent events
        """
        with self._lock:
            if limit:
                return self._event_history[-limit:]
            else:
                return self._event_history.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get notifier statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            enabled_count = sum(1 for obs in self.observers if obs.is_enabled())
            
            return {
                'total_observers': len(self.observers),
                'enabled_observers': enabled_count,
                'disabled_observers': len(self.observers) - enabled_count,
                'event_history_size': len(self._event_history),
                'observer_names': [obs.get_name() for obs in self.observers]
            }
    
    def __str__(self) -> str:
        """String representation of the notifier"""
        return f"SignalNotifier({self.get_observer_count()} observers)"
    
    def __repr__(self) -> str:
        """Detailed string representation of the notifier"""
        return f"SignalNotifier(observers={self.get_observer_count()}, history={len(self._event_history)})"
