"""
Market Data Repository Implementations

This module implements concrete market data repositories for database
and API data sources.
"""

from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import datetime
import json

from .base_repository import MarketDataRepository, RepositoryConfig
from ..strategies.base_strategy import MarketData
from app.db import SessionLocal, init_db
from app.services.data_sources import fetch_latest_1m
from app.services.candle_utils import load_candles_1m_df
from sqlalchemy import text
from app.services.debug import debug_helper


class DatabaseMarketDataRepository(MarketDataRepository):
    """
    Database implementation of market data repository.
    
    This repository accesses market data from the MySQL database.
    """
    
    def __init__(self, config: RepositoryConfig):
        """
        Initialize database market data repository.
        
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
            debug_helper.log_step("Database availability check failed", error=e)
            return False
    
    def get_candles(self, 
                   symbol: str, 
                   timeframe: str, 
                   limit: int = 1000,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Get candle data from database.
        
        Args:
            symbol: Symbol ticker
            timeframe: Timeframe (e.g., '1m', '5m', '1h')
            limit: Maximum number of candles to return
            start_date: Start date for data range
            end_date: End date for data range
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Get symbol_id
            symbol_id = self._get_symbol_id(symbol)
            if symbol_id is None:
                debug_helper.log_step(f"Symbol not found in database: {symbol}")
                return pd.DataFrame()
            
            # Check cache first
            cache_key = self.get_cache_key(
                "get_candles", 
                symbol=symbol, 
                timeframe=timeframe, 
                limit=limit,
                start_date=start_date.isoformat() if start_date else None,
                end_date=end_date.isoformat() if end_date else None
            )
            
            cached_data = self.get_from_cache(cache_key)
            if cached_data is not None:
                debug_helper.log_step(f"Retrieved cached candles for {symbol} {timeframe}")
                return cached_data
            
            # Query database
            with SessionLocal() as s:
                if timeframe == '1m':
                    # Query from candles_1m table
                    query = """
                        SELECT ts, open, high, low, close, volume
                        FROM candles_1m
                        WHERE symbol_id = :symbol_id
                    """
                    params = {'symbol_id': symbol_id}
                else:
                    # Query from candles_tf table
                    query = """
                        SELECT ts, open, high, low, close, volume
                        FROM candles_tf
                        WHERE symbol_id = :symbol_id AND timeframe = :timeframe
                    """
                    params = {'symbol_id': symbol_id, 'timeframe': timeframe}
                
                # Add date filters
                if start_date:
                    query += " AND ts >= :start_date"
                    params['start_date'] = start_date
                
                if end_date:
                    query += " AND ts <= :end_date"
                    params['end_date'] = end_date
                
                # Add ordering and limit
                query += " ORDER BY ts DESC LIMIT :limit"
                params['limit'] = limit
                
                rows = s.execute(text(query), params).fetchall()
            
            if not rows:
                debug_helper.log_step(f"No candles found for {symbol} {timeframe}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(rows, columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
            df = df.set_index(pd.DatetimeIndex(pd.to_datetime(df['ts'], utc=True))).drop(columns=['ts'])
            
            # Cache the result
            self.set_cache(cache_key, df)
            
            debug_helper.log_step(
                f"Retrieved {len(df)} candles for {symbol} {timeframe} from database"
            )
            
            return df
            
        except Exception as e:
            debug_helper.log_step(f"Error getting candles for {symbol} {timeframe}", error=e)
            return pd.DataFrame()
    
    def get_latest_candles(self, 
                          symbol: str, 
                          timeframe: str, 
                          count: int = 1) -> pd.DataFrame:
        """
        Get latest candle data from database.
        
        Args:
            symbol: Symbol ticker
            timeframe: Timeframe
            count: Number of latest candles to return
            
        Returns:
            DataFrame with latest OHLCV data
        """
        return self.get_candles(symbol, timeframe, limit=count)
    
    def save_candles(self, 
                    symbol: str, 
                    timeframe: str, 
                    candles: pd.DataFrame) -> bool:
        """
        Save candle data to database.
        
        Args:
            symbol: Symbol ticker
            timeframe: Timeframe
            candles: DataFrame with OHLCV data
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            if candles.empty:
                debug_helper.log_step(f"No candles to save for {symbol} {timeframe}")
                return True
            
            # Get symbol_id
            symbol_id = self._get_symbol_id(symbol)
            if symbol_id is None:
                debug_helper.log_step(f"Symbol not found in database: {symbol}")
                return False
            
            with SessionLocal() as s:
                if timeframe == '1m':
                    # Save to candles_1m table
                    for ts, row in candles.iterrows():
                        s.execute(text("""
                            INSERT INTO candles_1m (symbol_id, ts, open, high, low, close, volume)
                            VALUES (:symbol_id, :ts, :open, :high, :low, :close, :volume)
                            ON DUPLICATE KEY UPDATE 
                                open = VALUES(open), high = VALUES(high), low = VALUES(low),
                                close = VALUES(close), volume = VALUES(volume)
                        """), {
                            'symbol_id': symbol_id,
                            'ts': ts.to_pydatetime(),
                            'open': float(row['open']),
                            'high': float(row['high']),
                            'low': float(row['low']),
                            'close': float(row['close']),
                            'volume': float(row['volume'])
                        })
                else:
                    # Save to candles_tf table
                    for ts, row in candles.iterrows():
                        s.execute(text("""
                            INSERT INTO candles_tf (symbol_id, timeframe, ts, open, high, low, close, volume)
                            VALUES (:symbol_id, :timeframe, :ts, :open, :high, :low, :close, :volume)
                            ON DUPLICATE KEY UPDATE 
                                open = VALUES(open), high = VALUES(high), low = VALUES(low),
                                close = VALUES(close), volume = VALUES(volume)
                        """), {
                            'symbol_id': symbol_id,
                            'timeframe': timeframe,
                            'ts': ts.to_pydatetime(),
                            'open': float(row['open']),
                            'high': float(row['high']),
                            'low': float(row['low']),
                            'close': float(row['close']),
                            'volume': float(row['volume'])
                        })
                
                s.commit()
            
            # Clear cache for this symbol/timeframe
            cache_key_pattern = f"get_candles|symbol={symbol}|timeframe={timeframe}"
            keys_to_clear = [key for key in self._cache.keys() if key.startswith(cache_key_pattern)]
            for key in keys_to_clear:
                self.clear_cache(key)
            
            debug_helper.log_step(
                f"Saved {len(candles)} candles for {symbol} {timeframe} to database"
            )
            
            return True
            
        except Exception as e:
            debug_helper.log_step(f"Error saving candles for {symbol} {timeframe}", error=e)
            return False
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get symbol information from database.
        
        Args:
            symbol: Symbol ticker
            
        Returns:
            Dictionary with symbol information or None if not found
        """
        try:
            with SessionLocal() as s:
                row = s.execute(text("""
                    SELECT id, ticker, exchange, active, created_at, updated_at
                    FROM symbols
                    WHERE ticker = :ticker
                """), {'ticker': symbol}).fetchone()
                
                if row:
                    return {
                        'id': row[0],
                        'ticker': row[1],
                        'exchange': row[2],
                        'active': bool(row[3]),
                        'created_at': row[4],
                        'updated_at': row[5]
                    }
                else:
                    return None
                    
        except Exception as e:
            debug_helper.log_step(f"Error getting symbol info for {symbol}", error=e)
            return None
    
    def get_active_symbols(self) -> List[Dict[str, Any]]:
        """
        Get list of active symbols from database.
        
        Returns:
            List of dictionaries with symbol information
        """
        try:
            with SessionLocal() as s:
                rows = s.execute(text("""
                    SELECT id, ticker, exchange, active, created_at, updated_at
                    FROM symbols
                    WHERE active = 1
                    ORDER BY ticker
                """)).fetchall()
                
                symbols = []
                for row in rows:
                    symbols.append({
                        'id': row[0],
                        'ticker': row[1],
                        'exchange': row[2],
                        'active': bool(row[3]),
                        'created_at': row[4],
                        'updated_at': row[5]
                    })
                
                debug_helper.log_step(f"Retrieved {len(symbols)} active symbols from database")
                return symbols
                
        except Exception as e:
            debug_helper.log_step("Error getting active symbols", error=e)
            return []
    
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


class APIMarketDataRepository(MarketDataRepository):
    """
    API implementation of market data repository.
    
    This repository fetches market data from external APIs.
    """
    
    def __init__(self, config: RepositoryConfig):
        """
        Initialize API market data repository.
        
        Args:
            config: Repository configuration with API key
        """
        super().__init__(config)
        self.api_key = config.api_key
    
    def is_available(self) -> bool:
        """
        Check if API is available.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Simple availability check - could be enhanced
            return self.api_key is not None and len(self.api_key) > 0
        except Exception:
            return False
    
    def get_candles(self, 
                   symbol: str, 
                   timeframe: str, 
                   limit: int = 1000,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Get candle data from API.
        
        Args:
            symbol: Symbol ticker
            timeframe: Timeframe
            limit: Maximum number of candles to return
            start_date: Start date for data range
            end_date: End date for data range
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Check cache first
            cache_key = self.get_cache_key(
                "get_candles_api", 
                symbol=symbol, 
                timeframe=timeframe, 
                limit=limit,
                start_date=start_date.isoformat() if start_date else None,
                end_date=end_date.isoformat() if end_date else None
            )
            
            cached_data = self.get_from_cache(cache_key)
            if cached_data is not None:
                debug_helper.log_step(f"Retrieved cached API candles for {symbol} {timeframe}")
                return cached_data
            
            # For now, return empty DataFrame as API implementation would go here
            # In real implementation, this would call external APIs like:
            # - Yahoo Finance API
            # - Alpha Vantage API
            # - Polygon API
            # - etc.
            
            debug_helper.log_step(f"API candles not implemented for {symbol} {timeframe}")
            return pd.DataFrame()
            
        except Exception as e:
            debug_helper.log_step(f"Error getting API candles for {symbol} {timeframe}", error=e)
            return pd.DataFrame()
    
    def get_latest_candles(self, 
                          symbol: str, 
                          timeframe: str, 
                          count: int = 1) -> pd.DataFrame:
        """
        Get latest candle data from API.
        
        Args:
            symbol: Symbol ticker
            timeframe: Timeframe
            count: Number of latest candles to return
            
        Returns:
            DataFrame with latest OHLCV data
        """
        return self.get_candles(symbol, timeframe, limit=count)
    
    def save_candles(self, 
                    symbol: str, 
                    timeframe: str, 
                    candles: pd.DataFrame) -> bool:
        """
        Save candle data (API repositories typically don't save data).
        
        Args:
            symbol: Symbol ticker
            timeframe: Timeframe
            candles: DataFrame with OHLCV data
            
        Returns:
            False (API repositories don't save data)
        """
        debug_helper.log_step(f"API repository does not save data for {symbol} {timeframe}")
        return False
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get symbol information from API.
        
        Args:
            symbol: Symbol ticker
            
        Returns:
            Dictionary with symbol information or None if not found
        """
        try:
            # For now, return basic info
            # In real implementation, this would call API to get symbol details
            return {
                'ticker': symbol,
                'exchange': 'UNKNOWN',
                'active': True,
                'source': 'API'
            }
            
        except Exception as e:
            debug_helper.log_step(f"Error getting API symbol info for {symbol}", error=e)
            return None
    
    def get_active_symbols(self) -> List[Dict[str, Any]]:
        """
        Get list of active symbols from API.
        
        Returns:
            List of dictionaries with symbol information
        """
        try:
            # For now, return empty list
            # In real implementation, this would call API to get available symbols
            debug_helper.log_step("API active symbols not implemented")
            return []
            
        except Exception as e:
            debug_helper.log_step("Error getting API active symbols", error=e)
            return []
