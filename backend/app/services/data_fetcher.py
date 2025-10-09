"""
Data Fetcher Service
Handles data retrieval for various sources
"""

import logging
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class DataFetcher:
    """Service for fetching market data"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def fetch_symbol_data(self, symbol: str, period: str = '1y') -> Optional[pd.DataFrame]:
        """Fetch data for a symbol"""
        try:
            # Check cache first
            cache_key = f"{symbol}_{period}"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                    return cached_data
            
            # Fetch from yfinance
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if data is None or data.empty:
                logger.warning(f"No data available for symbol: {symbol}")
                return None
            
            # Cache the data
            self.cache[cache_key] = (data, datetime.now())
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def fetch_multi_timeframe_data(self, symbol: str, timeframes: list, period: str = '1y') -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple timeframes"""
        data = {}
        
        for tf in timeframes:
            try:
                # Convert timeframe to yfinance interval
                interval_map = {
                    '1m': '1m',
                    '2m': '2m',
                    '5m': '5m',
                    '15m': '15m',
                    '30m': '30m',
                    '1h': '1h',
                    '4h': '4h',
                    '1d': '1d'
                }
                
                interval = interval_map.get(tf, '1d')
                
                # Fetch data
                ticker = yf.Ticker(symbol)
                tf_data = ticker.history(period=period, interval=interval)
                
                if tf_data is not None and not tf_data.empty:
                    data[tf] = tf_data
                else:
                    logger.warning(f"No data available for {symbol} timeframe {tf}")
                    
            except Exception as e:
                logger.error(f"Error fetching {tf} data for {symbol}: {str(e)}")
                continue
        
        return data
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price for a symbol"""
        try:
            data = self.fetch_symbol_data(symbol, '1d')
            if data is not None and not data.empty:
                return float(data['Close'].iloc[-1])
            return None
        except Exception as e:
            logger.error(f"Error getting latest price for {symbol}: {str(e)}")
            return None
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', 0),
                'currency': info.get('currency', 'USD')
            }
            
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {str(e)}")
            return None
    
    def clear_cache(self):
        """Clear data cache"""
        self.cache.clear()
        logger.info("Data cache cleared")
