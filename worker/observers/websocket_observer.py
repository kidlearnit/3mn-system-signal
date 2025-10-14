"""
WebSocket Observer Implementation

This module implements the WebSocket observer for publishing trading signals
to WebSocket clients in real-time.
"""

import json
import redis
from typing import Optional, Dict, Any
from datetime import datetime
import os

from .base_observer import SignalObserver, SignalEvent
from app.services.debug import debug_helper


class WebSocketObserver(SignalObserver):
    """
    WebSocket observer for publishing trading signals to WebSocket clients.
    
    This observer publishes trading signals to Redis channels for real-time
    WebSocket clients to consume.
    """
    
    def __init__(self, 
                 redis_url: Optional[str] = None,
                 channel: str = "trading_signals",
                 name: Optional[str] = None):
        """
        Initialize WebSocket observer.
        
        Args:
            redis_url: Redis connection URL
            channel: Redis channel name for publishing
            name: Optional observer name
        """
        super().__init__(name)
        
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://redis:6379/0')
        self.channel = channel
        self._redis_client = None
        self._connected = False
        
        # Initialize Redis connection
        self._connect_redis()
    
    def _connect_redis(self) -> bool:
        """
        Connect to Redis.
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            self._redis_client = redis.from_url(self.redis_url)
            # Test connection
            self._redis_client.ping()
            self._connected = True
            debug_helper.log_step(f"WebSocket observer connected to Redis: {self.redis_url}")
            return True
        except Exception as e:
            debug_helper.log_step(f"WebSocket observer Redis connection failed: {e}")
            self._connected = False
            return False
    
    def handle_signal(self, event: SignalEvent) -> bool:
        """
        Handle a signal event by publishing it to WebSocket clients.
        
        Args:
            event: Signal event to handle
            
        Returns:
            True if message was published successfully, False otherwise
        """
        try:
            if not self._connected:
                if not self._connect_redis():
                    return False
            
            # Format the message
            message = self._format_websocket_message(event)
            
            # Publish to Redis channel
            success = self._publish_to_redis(message)
            
            if success:
                debug_helper.log_step(
                    f"Published WebSocket signal for {event.signal.symbol}: {event.signal.signal_type}"
                )
            else:
                debug_helper.log_step(
                    f"Failed to publish WebSocket signal for {event.signal.symbol}"
                )
            
            return success
            
        except Exception as e:
            debug_helper.log_step(f"Error handling WebSocket signal for {event.signal.symbol}", error=e)
            return False
    
    def _format_websocket_message(self, event: SignalEvent) -> Dict[str, Any]:
        """
        Format signal event into WebSocket message.
        
        Args:
            event: Signal event
            
        Returns:
            Formatted message dictionary
        """
        try:
            signal = event.signal
            
            message = {
                'type': 'trading_signal',
                'event_type': event.event_type,
                'timestamp': event.timestamp.isoformat(),
                'signal': {
                    'symbol': signal.symbol,
                    'signal_type': signal.signal_type,
                    'confidence': signal.confidence,
                    'strength': signal.strength,
                    'timeframe': signal.timeframe,
                    'strategy_name': signal.strategy_name,
                    'details': signal.details
                },
                'metadata': event.metadata
            }
            
            return message
            
        except Exception as e:
            debug_helper.log_step(f"Error formatting WebSocket message: {e}")
            return {
                'type': 'trading_signal',
                'event_type': event.event_type,
                'timestamp': event.timestamp.isoformat(),
                'signal': {
                    'symbol': event.signal.symbol,
                    'signal_type': event.signal.signal_type,
                    'confidence': event.signal.confidence,
                    'strength': event.signal.strength
                }
            }
    
    def _publish_to_redis(self, message: Dict[str, Any]) -> bool:
        """
        Publish message to Redis channel.
        
        Args:
            message: Message to publish
            
        Returns:
            True if published successfully, False otherwise
        """
        try:
            message_json = json.dumps(message)
            result = self._redis_client.publish(self.channel, message_json)
            
            # Redis publish returns the number of clients that received the message
            return result >= 0
            
        except Exception as e:
            debug_helper.log_step(f"Error publishing to Redis: {e}")
            return False
    
    def set_redis_url(self, redis_url: str) -> None:
        """
        Set Redis connection URL.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self._connect_redis()
    
    def set_channel(self, channel: str) -> None:
        """
        Set Redis channel name.
        
        Args:
            channel: Channel name
        """
        self.channel = channel
    
    def test_connection(self) -> bool:
        """
        Test Redis connection.
        
        Returns:
            True if connection is working, False otherwise
        """
        try:
            if not self._connected:
                return self._connect_redis()
            
            # Test publish
            test_message = {
                'type': 'test',
                'timestamp': datetime.now().isoformat(),
                'message': 'WebSocket observer connection test'
            }
            
            return self._publish_to_redis(test_message)
            
        except Exception as e:
            debug_helper.log_step(f"WebSocket connection test failed: {e}")
            return False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get connection status information.
        
        Returns:
            Dictionary with connection status
        """
        return {
            'connected': self._connected,
            'redis_url': self.redis_url,
            'channel': self.channel,
            'client_available': self._redis_client is not None
        }


class WebSocketMarketObserver(WebSocketObserver):
    """
    Enhanced WebSocket observer with market-specific channels.
    
    This observer publishes signals to different channels based on market
    and provides enhanced message formatting.
    """
    
    def __init__(self, 
                 redis_url: Optional[str] = None,
                 market: str = "US",
                 name: Optional[str] = None):
        """
        Initialize WebSocket market observer.
        
        Args:
            redis_url: Redis connection URL
            market: Market type ("US", "VN", etc.)
            name: Optional observer name
        """
        # Set market-specific channel
        channel = f"trading_signals_{market.lower()}"
        super().__init__(redis_url, channel, name)
        
        self.market = market
    
    def _format_websocket_message(self, event: SignalEvent) -> Dict[str, Any]:
        """
        Format signal event with market-specific information.
        
        Args:
            event: Signal event
            
        Returns:
            Formatted message dictionary
        """
        try:
            # Get base message
            message = super()._format_websocket_message(event)
            
            # Add market-specific information
            message['market'] = self.market
            message['market_channel'] = self.channel
            
            # Add market-specific metadata
            if 'market_metadata' not in message['metadata']:
                message['metadata']['market_metadata'] = {}
            
            message['metadata']['market_metadata'].update({
                'market': self.market,
                'channel': self.channel,
                'timestamp': datetime.now().isoformat()
            })
            
            return message
            
        except Exception as e:
            debug_helper.log_step(f"Error formatting market WebSocket message: {e}")
            return super()._format_websocket_message(event)


class WebSocketMultiChannelObserver(WebSocketObserver):
    """
    WebSocket observer that publishes to multiple channels.
    
    This observer can publish the same signal to multiple Redis channels
    for different types of clients or applications.
    """
    
    def __init__(self, 
                 redis_url: Optional[str] = None,
                 channels: Optional[list] = None,
                 name: Optional[str] = None):
        """
        Initialize WebSocket multi-channel observer.
        
        Args:
            redis_url: Redis connection URL
            channels: List of channel names
            name: Optional observer name
        """
        # Use first channel as default
        default_channel = channels[0] if channels else "trading_signals"
        super().__init__(redis_url, default_channel, name)
        
        self.channels = channels or ["trading_signals"]
    
    def handle_signal(self, event: SignalEvent) -> bool:
        """
        Handle a signal event by publishing to multiple channels.
        
        Args:
            event: Signal event to handle
            
        Returns:
            True if message was published to at least one channel, False otherwise
        """
        try:
            if not self._connected:
                if not self._connect_redis():
                    return False
            
            # Format the message
            message = self._format_websocket_message(event)
            message_json = json.dumps(message)
            
            # Publish to all channels
            success_count = 0
            for channel in self.channels:
                try:
                    result = self._redis_client.publish(channel, message_json)
                    if result >= 0:
                        success_count += 1
                except Exception as e:
                    debug_helper.log_step(f"Error publishing to channel {channel}: {e}")
            
            success = success_count > 0
            
            if success:
                debug_helper.log_step(
                    f"Published WebSocket signal to {success_count}/{len(self.channels)} channels "
                    f"for {event.signal.symbol}: {event.signal.signal_type}"
                )
            else:
                debug_helper.log_step(
                    f"Failed to publish WebSocket signal to any channel for {event.signal.symbol}"
                )
            
            return success
            
        except Exception as e:
            debug_helper.log_step(f"Error handling multi-channel WebSocket signal for {event.signal.symbol}", error=e)
            return False
    
    def add_channel(self, channel: str) -> None:
        """
        Add a channel to the list.
        
        Args:
            channel: Channel name to add
        """
        if channel not in self.channels:
            self.channels.append(channel)
    
    def remove_channel(self, channel: str) -> None:
        """
        Remove a channel from the list.
        
        Args:
            channel: Channel name to remove
        """
        if channel in self.channels:
            self.channels.remove(channel)
    
    def get_channels(self) -> list:
        """
        Get list of channels.
        
        Returns:
            List of channel names
        """
        return self.channels.copy()
