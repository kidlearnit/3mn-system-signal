"""
Data Fetch Step

This module implements data fetching step for the processing pipeline.
"""

from typing import Optional
import pandas as pd
from datetime import datetime

from .base_pipeline import ProcessingStep
from ..strategies.base_strategy import MarketData
from app.services.data_sources import fetch_latest_1m
from app.services.candle_utils import load_candles_1m_df
from app.services.debug import debug_helper


class DataFetchStep(ProcessingStep):
    """
    Data fetching step for the processing pipeline.
    
    This step fetches market data from various sources (API, database)
    and prepares it for further processing.
    """
    
    def __init__(self, 
                 source: str = "auto",
                 lookback_minutes: int = 1440,
                 name: Optional[str] = None):
        """
        Initialize data fetch step.
        
        Args:
            source: Data source ("auto", "api", "database")
            lookback_minutes: Number of minutes to look back for data
            name: Optional step name
        """
        super().__init__(name)
        
        self.source = source
        self.lookback_minutes = lookback_minutes
        
        self.set_parameter('source', source)
        self.set_parameter('lookback_minutes', lookback_minutes)
    
    def process(self, data: MarketData) -> MarketData:
        """
        Fetch market data from configured source.
        
        Args:
            data: Input market data (may be empty or partial)
            
        Returns:
            Market data with fetched candles
            
        Raises:
            ValueError: If data fetching fails
        """
        try:
            # Log fetch start
            debug_helper.log_step(
                f"Data fetch for {data.symbol}",
                {
                    'source': self.source,
                    'lookback_minutes': self.lookback_minutes,
                    'exchange': data.exchange,
                    'timeframe': data.timeframe
                }
            )
            
            # Fetch data based on source
            if self.source == "api":
                candles = self._fetch_from_api(data)
            elif self.source == "database":
                candles = self._fetch_from_database(data)
            elif self.source == "auto":
                candles = self._fetch_auto(data)
            else:
                raise ValueError(f"Unknown data source: {self.source}")
            
            if candles is None or candles.empty:
                raise ValueError(f"No data fetched for {data.symbol}")
            
            # Update data with fetched candles
            data.candles = candles
            data.timestamp = datetime.now()
            
            # Log successful fetch
            debug_helper.log_step(
                f"Data fetch successful for {data.symbol}",
                {
                    'candles_count': len(candles),
                    'date_range': f"{candles.index[0]} to {candles.index[-1]}" if not candles.empty else "empty",
                    'source': self.source
                }
            )
            
            return data
            
        except Exception as e:
            error_msg = f"Data fetch failed for {data.symbol}: {str(e)}"
            debug_helper.log_step(f"Data fetch error for {data.symbol}", error=e)
            raise ValueError(error_msg)
    
    def get_name(self) -> str:
        """Get step name"""
        return "DataFetch"
    
    def _fetch_from_api(self, data: MarketData) -> Optional[pd.DataFrame]:
        """
        Fetch data from API.
        
        Args:
            data: Market data object
            
        Returns:
            DataFrame with candle data or None if fetch fails
        """
        try:
            # This would need symbol_id - for now, we'll use a placeholder
            # In real implementation, you'd need to get symbol_id from data
            symbol_id = self._get_symbol_id(data.symbol, data.exchange)
            
            if symbol_id is None:
                print(f"⚠️ Could not get symbol_id for {data.symbol}")
                return None
            
            # Fetch latest data from API
            count = fetch_latest_1m(symbol_id, data.symbol, data.exchange)
            
            if count > 0:
                # Load the fetched data
                candles = load_candles_1m_df(symbol_id, self.lookback_minutes)
                return candles
            else:
                print(f"⚠️ No new data fetched from API for {data.symbol}")
                return None
                
        except Exception as e:
            print(f"❌ API fetch error for {data.symbol}: {e}")
            return None
    
    def _fetch_from_database(self, data: MarketData) -> Optional[pd.DataFrame]:
        """
        Fetch data from database.
        
        Args:
            data: Market data object
            
        Returns:
            DataFrame with candle data or None if fetch fails
        """
        try:
            # Get symbol_id
            symbol_id = self._get_symbol_id(data.symbol, data.exchange)
            
            if symbol_id is None:
                print(f"⚠️ Could not get symbol_id for {data.symbol}")
                return None
            
            # Load data from database
            candles = load_candles_1m_df(symbol_id, self.lookback_minutes)
            
            if candles.empty:
                print(f"⚠️ No data found in database for {data.symbol}")
                return None
            
            return candles
            
        except Exception as e:
            print(f"❌ Database fetch error for {data.symbol}: {e}")
            return None
    
    def _fetch_auto(self, data: MarketData) -> Optional[pd.DataFrame]:
        """
        Fetch data using automatic source selection.
        
        Args:
            data: Market data object
            
        Returns:
            DataFrame with candle data or None if fetch fails
        """
        try:
            # Try API first
            candles = self._fetch_from_api(data)
            
            if candles is not None and not candles.empty:
                return candles
            
            # Fall back to database
            print(f"⚠️ API fetch failed for {data.symbol}, trying database")
            candles = self._fetch_from_database(data)
            
            if candles is not None and not candles.empty:
                return candles
            
            print(f"⚠️ Both API and database fetch failed for {data.symbol}")
            return None
            
        except Exception as e:
            print(f"❌ Auto fetch error for {data.symbol}: {e}")
            return None
    
    def _get_symbol_id(self, symbol: str, exchange: str) -> Optional[int]:
        """
        Get symbol_id from database.
        
        Args:
            symbol: Symbol ticker
            exchange: Exchange name
            
        Returns:
            Symbol ID or None if not found
        """
        try:
            from app.db import SessionLocal
            from sqlalchemy import text
            
            with SessionLocal() as s:
                result = s.execute(text("""
                    SELECT id FROM symbols 
                    WHERE ticker = :ticker AND exchange = :exchange
                """), {'ticker': symbol, 'exchange': exchange}).fetchone()
                
                if result:
                    return result[0]
                else:
                    return None
                    
        except Exception as e:
            print(f"❌ Error getting symbol_id for {symbol}: {e}")
            return None
    
    def set_source(self, source: str) -> None:
        """
        Set data source.
        
        Args:
            source: Data source ("auto", "api", "database")
        """
        if source not in ["auto", "api", "database"]:
            raise ValueError("Source must be 'auto', 'api', or 'database'")
        
        self.source = source
        self.set_parameter('source', source)
    
    def set_lookback_minutes(self, lookback_minutes: int) -> None:
        """
        Set lookback minutes.
        
        Args:
            lookback_minutes: Number of minutes to look back
        """
        if lookback_minutes <= 0:
            raise ValueError("Lookback minutes must be positive")
        
        self.lookback_minutes = lookback_minutes
        self.set_parameter('lookback_minutes', lookback_minutes)
