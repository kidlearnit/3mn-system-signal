"""
Strategy Pattern Implementation for Trading Signals

This module provides abstract base classes and concrete implementations
for different trading signal strategies (MACD, SMA, Hybrid, etc.)
"""

from .base_strategy import SignalStrategy, MarketData, Signal
from .macd_strategy import MACDStrategy
from .sma_strategy import SMAStrategy

__all__ = [
    'SignalStrategy',
    'MarketData', 
    'Signal',
    'MACDStrategy',
    'SMAStrategy'
]
