"""
Signal Repository Implementations

This module implements concrete signal repositories for storing
and retrieving trading signals.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from .base_repository import SignalRepository, RepositoryConfig
from ..strategies.base_strategy import Signal
from app.db import SessionLocal, init_db
from sqlalchemy import text
from app.services.debug import debug_helper


class DatabaseSignalRepository(SignalRepository):
    """
    Database implementation of signal repository.
    
    This repository stores and retrieves trading signals from the MySQL database.
    """
    
    def __init__(self, config: RepositoryConfig):
        """
        Initialize database signal repository.
        
        Args:
            config: Repository configuration with connection string
        """
        super().__init__(config)
        
        # Initialize database connection
        if config.connection_string:
            init_db(config.connection_string)
    
    def is_available(self) -> bool:
        """
        Check if database is available.
        
        Returns:
            True if database is accessible, False otherwise
        """
        try:
            with SessionLocal() as s:
                s.execute(text("SELECT 1")).fetchone()
            return True
        except Exception as e:
            debug_helper.log_step("Signal repository database availability check failed", error=e)
            return False
    
    def save_signal(self, signal: Signal) -> bool:
        """
        Save a trading signal to database.
        
        Args:
            signal: Signal object to save
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Get symbol_id
            symbol_id = self._get_symbol_id(signal.symbol)
            if symbol_id is None:
                debug_helper.log_step(f"Symbol not found for signal: {signal.symbol}")
                return False
            
            # Get strategy_id (create if not exists)
            strategy_id = self._get_or_create_strategy_id(signal.strategy_name)
            
            with SessionLocal() as s:
                s.execute(text("""
                    INSERT INTO signals (symbol_id, timeframe, ts, strategy_id, signal_type, details)
                    VALUES (:symbol_id, :timeframe, :ts, :strategy_id, :signal_type, :details)
                """), {
                    'symbol_id': symbol_id,
                    'timeframe': signal.timeframe,
                    'ts': signal.timestamp,
                    'strategy_id': strategy_id,
                    'signal_type': signal.signal_type,
                    'details': json.dumps({
                        'confidence': signal.confidence,
                        'strength': signal.strength,
                        'strategy_name': signal.strategy_name,
                        'details': signal.details
                    })
                })
                s.commit()
            
            debug_helper.log_step(
                f"Saved signal for {signal.symbol}: {signal.signal_type} "
                f"(confidence: {signal.confidence:.3f})"
            )
            
            return True
            
        except Exception as e:
            debug_helper.log_step(f"Error saving signal for {signal.symbol}", error=e)
            return False
    
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
        try:
            with SessionLocal() as s:
                query = """
                    SELECT s.symbol_id, sym.ticker, s.timeframe, s.ts, s.strategy_id, 
                           s.signal_type, s.details, st.name as strategy_name
                    FROM signals s
                    JOIN symbols sym ON s.symbol_id = sym.id
                    LEFT JOIN strategies st ON s.strategy_id = st.id
                    WHERE 1=1
                """
                params = {}
                
                if symbol:
                    query += " AND sym.ticker = :symbol"
                    params['symbol'] = symbol
                
                if signal_type:
                    query += " AND s.signal_type = :signal_type"
                    params['signal_type'] = signal_type
                
                if start_date:
                    query += " AND s.ts >= :start_date"
                    params['start_date'] = start_date
                
                if end_date:
                    query += " AND s.ts <= :end_date"
                    params['end_date'] = end_date
                
                query += " ORDER BY s.ts DESC LIMIT :limit"
                params['limit'] = limit
                
                rows = s.execute(text(query), params).fetchall()
            
            signals = []
            for row in rows:
                try:
                    details = json.loads(row[6]) if row[6] else {}
                    
                    signal = Signal(
                        symbol=row[1],  # ticker
                        signal_type=row[5],  # signal_type
                        confidence=details.get('confidence', 0.0),
                        strength=details.get('strength', 0.0),
                        timeframe=row[2],  # timeframe
                        timestamp=row[3],  # ts
                        strategy_name=row[7] or details.get('strategy_name', 'Unknown'),
                        details=details.get('details', {})
                    )
                    signals.append(signal)
                    
                except Exception as e:
                    debug_helper.log_step(f"Error parsing signal row: {e}")
                    continue
            
            debug_helper.log_step(f"Retrieved {len(signals)} signals from database")
            return signals
            
        except Exception as e:
            debug_helper.log_step("Error getting signals from database", error=e)
            return []
    
    def get_latest_signal(self, symbol: str) -> Optional[Signal]:
        """
        Get the latest signal for a symbol.
        
        Args:
            symbol: Symbol ticker
            
        Returns:
            Latest Signal object or None if not found
        """
        try:
            signals = self.get_signals(symbol=symbol, limit=1)
            return signals[0] if signals else None
            
        except Exception as e:
            debug_helper.log_step(f"Error getting latest signal for {symbol}", error=e)
            return None
    
    def delete_old_signals(self, days: int = 30) -> int:
        """
        Delete old signals.
        
        Args:
            days: Delete signals older than this many days
            
        Returns:
            Number of signals deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with SessionLocal() as s:
                result = s.execute(text("""
                    DELETE FROM signals WHERE ts < :cutoff_date
                """), {'cutoff_date': cutoff_date})
                
                deleted_count = result.rowcount
                s.commit()
            
            debug_helper.log_step(f"Deleted {deleted_count} old signals (older than {days} days)")
            return deleted_count
            
        except Exception as e:
            debug_helper.log_step("Error deleting old signals", error=e)
            return 0
    
    def _get_symbol_id(self, symbol: str) -> Optional[int]:
        """
        Get symbol ID from database.
        
        Args:
            symbol: Symbol ticker
            
        Returns:
            Symbol ID or None if not found
        """
        try:
            with SessionLocal() as s:
                result = s.execute(text("""
                    SELECT id FROM symbols WHERE ticker = :ticker
                """), {'ticker': symbol}).fetchone()
                
                return result[0] if result else None
                
        except Exception as e:
            debug_helper.log_step(f"Error getting symbol_id for {symbol}", error=e)
            return None
    
    def _get_or_create_strategy_id(self, strategy_name: str) -> int:
        """
        Get or create strategy ID.
        
        Args:
            strategy_name: Strategy name
            
        Returns:
            Strategy ID
        """
        try:
            with SessionLocal() as s:
                # Try to get existing strategy
                result = s.execute(text("""
                    SELECT id FROM strategies WHERE name = :name
                """), {'name': strategy_name}).fetchone()
                
                if result:
                    return result[0]
                
                # Create new strategy
                s.execute(text("""
                    INSERT INTO strategies (name, description, created_at)
                    VALUES (:name, :description, :created_at)
                """), {
                    'name': strategy_name,
                    'description': f'Strategy: {strategy_name}',
                    'created_at': datetime.now()
                })
                s.commit()
                
                # Get the new strategy ID
                result = s.execute(text("""
                    SELECT id FROM strategies WHERE name = :name
                """), {'name': strategy_name}).fetchone()
                
                return result[0] if result else 1  # Default to 1 if something goes wrong
                
        except Exception as e:
            debug_helper.log_step(f"Error getting/creating strategy_id for {strategy_name}", error=e)
            return 1  # Default strategy ID
