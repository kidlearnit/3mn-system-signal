#!/usr/bin/env python3
"""
Candles REST API endpoints
"""

from flask import request
from .base_api import BaseAPI
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CandlesAPI(BaseAPI):
    """Candles REST API"""
    
    def __init__(self):
        super().__init__('candles', '/api/v1/candles')
        self._register_routes()
    
    def _register_routes(self):
        """Register candles routes"""
        
        @self.blueprint.route('/1m', methods=['GET'])
        def get_1m_candles():
            """Get 1-minute candles"""
            return self._get_candles('1m')
        
        @self.blueprint.route('/<timeframe>', methods=['GET'])
        def get_candles(timeframe):
            """Get candles for specific timeframe"""
            valid_timeframes = ['1m', '2m', '5m', '15m', '30m', '1h', '4h', '1D']
            if timeframe not in valid_timeframes:
                return self.error_response(f"Invalid timeframe. Valid options: {valid_timeframes}", 400)
            
            return self._get_candles(timeframe)
        
        @self.blueprint.route('/<int:symbol_id>/<timeframe>', methods=['GET'])
        def get_symbol_candles(symbol_id, timeframe):
            """Get candles for specific symbol and timeframe"""
            valid_timeframes = ['1m', '2m', '5m', '15m', '30m', '1h', '4h', '1D']
            if timeframe not in valid_timeframes:
                return self.error_response(f"Invalid timeframe. Valid options: {valid_timeframes}", 400)
            
            return self._get_candles(timeframe, symbol_id)
    
    def _get_candles(self, timeframe, symbol_id=None):
        """Get candles with pagination and filtering"""
        try:
            page, per_page = self.validate_pagination_params()
            
            # Determine table name
            if timeframe == '1m':
                table_name = 'candles_1m'
            else:
                table_name = 'candles_tf'
            
            # Build base query
            if timeframe == '1m':
                query = f"""
                    SELECT c.id, c.symbol_id, c.ts, c.open, c.high, c.low, c.close, c.volume,
                           s.ticker, s.exchange
                    FROM {table_name} c
                    JOIN symbols s ON c.symbol_id = s.id
                """
            else:
                query = f"""
                    SELECT c.id, c.symbol_id, c.timeframe, c.ts, c.open, c.high, c.low, c.close, c.volume,
                           s.ticker, s.exchange
                    FROM {table_name} c
                    JOIN symbols s ON c.symbol_id = s.id
                """
            
            # Build filter conditions
            conditions = []
            params = {}
            
            # Symbol filter
            if symbol_id:
                conditions.append("c.symbol_id = :symbol_id")
                params['symbol_id'] = symbol_id
            
            # Timeframe filter for candles_tf
            if timeframe != '1m':
                conditions.append("c.timeframe = :timeframe")
                params['timeframe'] = timeframe
            
            # Date range filters
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            if start_date:
                conditions.append("DATE(c.ts) >= :start_date")
                params['start_date'] = start_date
            
            if end_date:
                conditions.append("DATE(c.ts) <= :end_date")
                params['end_date'] = end_date
            
            # Symbol ticker filter
            symbol_ticker = request.args.get('symbol_ticker')
            if symbol_ticker:
                conditions.append("s.ticker = :symbol_ticker")
                params['symbol_ticker'] = symbol_ticker
            
            # Add WHERE clause if conditions exist
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            # Add ORDER BY
            query += " ORDER BY c.ts DESC"
            
            # Get paginated results
            result = self.paginate_query(query, params, page, per_page)
            return self.success_response(result)
            
        except Exception as e:
            logger.error(f"Error getting candles: {e}")
            return self.error_response(f"Failed to get candles: {str(e)}", 500)
        
        @self.blueprint.route('/stats', methods=['GET'])
        def get_candles_stats():
            """Get candles statistics"""
            try:
                # Get total 1m candles
                total_1m = self.execute_scalar("SELECT COUNT(*) FROM candles_1m")
                
                # Get total tf candles
                total_tf = self.execute_scalar("SELECT COUNT(*) FROM candles_tf")
                
                # Get candles by timeframe
                timeframes = self.execute_query("""
                    SELECT timeframe, COUNT(*) as count 
                    FROM candles_tf 
                    GROUP BY timeframe 
                    ORDER BY count DESC
                """)
                
                # Get top symbols by candle count
                top_symbols_1m = self.execute_query("""
                    SELECT s.ticker, COUNT(c.id) as candle_count
                    FROM candles_1m c
                    JOIN symbols s ON c.symbol_id = s.id
                    GROUP BY c.symbol_id, s.ticker
                    ORDER BY candle_count DESC
                    LIMIT 10
                """)
                
                # Get latest candle timestamps
                latest_1m = self.execute_scalar("SELECT MAX(ts) FROM candles_1m")
                latest_tf = self.execute_scalar("SELECT MAX(ts) FROM candles_tf")
                
                stats = {
                    'total_1m_candles': total_1m,
                    'total_tf_candles': total_tf,
                    'timeframes': timeframes,
                    'top_symbols_1m': top_symbols_1m,
                    'latest_1m_timestamp': latest_1m.isoformat() if latest_1m else None,
                    'latest_tf_timestamp': latest_tf.isoformat() if latest_tf else None
                }
                
                return self.success_response(stats)
                
            except Exception as e:
                logger.error(f"Error getting candles stats: {e}")
                return self.error_response(f"Failed to get candles stats: {str(e)}", 500)

# Create the API instance
candles_api = CandlesAPI()
