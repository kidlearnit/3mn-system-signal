"""
Repository Pattern Implementation for Data Access

This module provides abstract base classes and concrete implementations
for data access using the Repository pattern.
"""

from .base_repository import BaseRepository
from .market_data_repository import MarketDataRepository, DatabaseMarketDataRepository, APIMarketDataRepository
from .signal_repository import SignalRepository, DatabaseSignalRepository
from .workflow_repository import WorkflowRepository, DatabaseWorkflowRepository

__all__ = [
    'BaseRepository',
    'MarketDataRepository',
    'DatabaseMarketDataRepository', 
    'APIMarketDataRepository',
    'SignalRepository',
    'DatabaseSignalRepository',
    'WorkflowRepository',
    'DatabaseWorkflowRepository'
]
