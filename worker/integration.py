#!/usr/bin/env python3
"""
Integration module for signal notifications
Provides notify_signal function for backward compatibility
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def notify_signal(
    symbol: str,
    timeframe: str,
    signal_type: str,
    confidence: float,
    strength: float,
    strategy_name: str,
    details: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Notify about a signal - backward compatibility function
    
    Args:
        symbol: Symbol name (e.g., 'VN30')
        timeframe: Timeframe (e.g., '1m', 'multi')
        signal_type: Signal type (e.g., 'BUY', 'SELL')
        confidence: Confidence level (0.0-1.0)
        strength: Signal strength
        strategy_name: Strategy name
        details: Additional details
        
    Returns:
        True if notification was successful, False otherwise
    """
    try:
        logger.info(f"📢 Signal notification: {symbol} {signal_type} (confidence: {confidence:.2f})")
        
        # For now, just log the signal
        # In the future, this could integrate with the Observer pattern
        signal_data = {
            'symbol': symbol,
            'timeframe': timeframe,
            'signal_type': signal_type,
            'confidence': confidence,
            'strength': strength,
            'strategy_name': strategy_name,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Signal data: {signal_data}")
        
        # TODO: Integrate with Observer pattern or Telegram service
        # For VN30, the telegram notification is handled directly in worker_vn_macd.py
        
        return True
        
    except Exception as e:
        logger.error(f"Error in notify_signal: {e}")
        return False
