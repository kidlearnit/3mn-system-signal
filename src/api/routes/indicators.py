#!/usr/bin/env python3
"""
Indicators REST API endpoints
"""

from flask import request
from .base_api import BaseAPI
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class IndicatorsAPI(BaseAPI):
    """Indicators REST API"""
    
    def __init__(self):
        super().__init__('indicators', '/api/v1/indicators')
        self._register_routes()
    
    def _register_routes(self):
        """Register indicators routes"""
        
        @self.blueprint.route('/macd', methods=['GET'])
        def get_macd_indicators():
            """Get MACD indicators"""
            return self._get_indicators('macd')
        
        @self.blueprint.route('/bars', methods=['GET'])
        def get_bars_indicators():
            """Get Bars indicators"""
            return self._get_indicators('bars')
        
        @self.blueprint.route('/<int:symbol_id>/macd', methods=['GET'])
        def get_symbol_macd(symbol_id):
            """Get MACD indicators for specific symbol"""
            return self._get_indicators('macd', symbol_id)
        
        @self.blueprint.route('/<int:symbol_id>/bars', methods=['GET'])
        def get_symbol_bars(symbol_id):
            """Get Bars indicators for specific symbol"""
            return self._get_indicators('bars', symbol_id)
    
    def _get_indicators(self, indicator_type, symbol_id=None):
        """Get indicators with pagination and filtering"""
        try:
            page, per_page = self.validate_pagination_params()
            
            # Determine table name
            if indicator_type == 'macd':
                table_name = 'indicators_macd'
            elif indicator_type == 'bars':
                table_name = 'indicators_bars'
            else:
                return self.error_response("Invalid indicator type", 400)
            
            # Build base query
            if indicator_type == 'macd':
                query = f"""
                    SELECT i.id, i.symbol_id, i.timeframe, i.ts, i.macd, i.macd_signal, i.hist,
                           s.ticker, s.exchange
                    FROM {table_name} i
                    JOIN symbols s ON i.symbol_id = s.id
                """
            else:  # bars
                query = f"""
                    SELECT i.id, i.symbol_id, i.timeframe, i.ts, i.bars,
                           s.ticker, s.exchange
                    FROM {table_name} i
                    JOIN symbols s ON i.symbol_id = s.id
                """
            
            # Build filter conditions
            conditions = []
            params = {}
            
            # Symbol filter
            if symbol_id:
                conditions.append("i.symbol_id = :symbol_id")
                params['symbol_id'] = symbol_id
            
            # Timeframe filter
            timeframe = request.args.get('timeframe')
            if timeframe:
                conditions.append("i.timeframe = :timeframe")
                params['timeframe'] = timeframe
            
            # Date range filters
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            if start_date:
                conditions.append("DATE(i.ts) >= :start_date")
                params['start_date'] = start_date
            
            if end_date:
                conditions.append("DATE(i.ts) <= :end_date")
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
            query += " ORDER BY i.ts DESC"
            
            # Get paginated results
            result = self.paginate_query(query, params, page, per_page)
            return self.success_response(result)
            
        except Exception as e:
            logger.error(f"Error getting {indicator_type} indicators: {e}")
            return self.error_response(f"Failed to get {indicator_type} indicators: {str(e)}", 500)
        
        @self.blueprint.route('/stats', methods=['GET'])
        def get_indicators_stats():
            """Get indicators statistics"""
            try:
                # Get total MACD indicators
                total_macd = self.execute_scalar("SELECT COUNT(*) FROM indicators_macd")
                
                # Get total Bars indicators
                total_bars = self.execute_scalar("SELECT COUNT(*) FROM indicators_bars")
                
                # Get MACD by timeframe
                macd_timeframes = self.execute_query("""
                    SELECT timeframe, COUNT(*) as count 
                    FROM indicators_macd 
                    GROUP BY timeframe 
                    ORDER BY count DESC
                """)
                
                # Get Bars by timeframe
                bars_timeframes = self.execute_query("""
                    SELECT timeframe, COUNT(*) as count 
                    FROM indicators_bars 
                    GROUP BY timeframe 
                    ORDER BY count DESC
                """)
                
                # Get top symbols by indicator count
                top_symbols_macd = self.execute_query("""
                    SELECT s.ticker, COUNT(i.id) as indicator_count
                    FROM indicators_macd i
                    JOIN symbols s ON i.symbol_id = s.id
                    GROUP BY i.symbol_id, s.ticker
                    ORDER BY indicator_count DESC
                    LIMIT 10
                """)
                
                # Get latest indicator timestamps
                latest_macd = self.execute_scalar("SELECT MAX(ts) FROM indicators_macd")
                latest_bars = self.execute_scalar("SELECT MAX(ts) FROM indicators_bars")
                
                stats = {
                    'total_macd_indicators': total_macd,
                    'total_bars_indicators': total_bars,
                    'macd_timeframes': macd_timeframes,
                    'bars_timeframes': bars_timeframes,
                    'top_symbols_macd': top_symbols_macd,
                    'latest_macd_timestamp': latest_macd.isoformat() if latest_macd else None,
                    'latest_bars_timestamp': latest_bars.isoformat() if latest_bars else None
                }
                
                return self.success_response(stats)
                
            except Exception as e:
                logger.error(f"Error getting indicators stats: {e}")
                return self.error_response(f"Failed to get indicators stats: {str(e)}", 500)

# Create the API instance
indicators_api = IndicatorsAPI()
