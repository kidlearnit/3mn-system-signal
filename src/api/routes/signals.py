#!/usr/bin/env python3
"""
Signals REST API endpoints
"""

from flask import request
from .base_api import BaseAPI
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SignalsAPI(BaseAPI):
    """Signals REST API"""
    
    def __init__(self):
        super().__init__('signals', '/api/v1/signals')
        self._register_routes()
    
    def _register_routes(self):
        """Register signals routes"""
        
        @self.blueprint.route('', methods=['GET'])
        def get_signals():
            """Get all signals with pagination and filtering"""
            try:
                page, per_page = self.validate_pagination_params()
                
                # Build base query
                query = """
                    SELECT s.id, s.symbol_id, s.timeframe, s.ts, s.strategy_id,
                           s.signal_type, s.details,
                           sym.ticker, sym.exchange,
                           st.name as strategy_name
                    FROM signals s
                    JOIN symbols sym ON s.symbol_id = sym.id
                    JOIN trade_strategies st ON s.strategy_id = st.id
                """
                
                # Build filter conditions
                allowed_filters = ['symbol_id', 'timeframe', 'strategy_id', 'signal_type']
                conditions, params = self.build_filter_conditions(allowed_filters)
                
                # Add date range filters
                start_date = request.args.get('start_date')
                end_date = request.args.get('end_date')
                
                if start_date:
                    conditions.append("DATE(s.ts) >= :start_date")
                    params['start_date'] = start_date
                
                if end_date:
                    conditions.append("DATE(s.ts) <= :end_date")
                    params['end_date'] = end_date
                
                # Add symbol ticker filter
                symbol_ticker = request.args.get('symbol_ticker')
                if symbol_ticker:
                    conditions.append("sym.ticker = :symbol_ticker")
                    params['symbol_ticker'] = symbol_ticker
                
                # Add WHERE clause if conditions exist
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                # Add ORDER BY
                query += " ORDER BY s.ts DESC"
                
                # Get paginated results
                result = self.paginate_query(query, params, page, per_page)
                return self.success_response(result)
                
            except Exception as e:
                logger.error(f"Error getting signals: {e}")
                return self.error_response(f"Failed to get signals: {str(e)}", 500)
        
        @self.blueprint.route('/<int:signal_id>', methods=['GET'])
        def get_signal(signal_id):
            """Get signal by ID"""
            try:
                query = """
                    SELECT s.id, s.symbol_id, s.timeframe, s.ts, s.strategy_id,
                           s.signal_type, s.details,
                           sym.ticker, sym.exchange,
                           st.name as strategy_name
                    FROM signals s
                    JOIN symbols sym ON s.symbol_id = sym.id
                    JOIN trade_strategies st ON s.strategy_id = st.id
                    WHERE s.id = :signal_id
                """
                
                result = self.execute_query(query, {'signal_id': signal_id})
                
                if not result:
                    return self.error_response("Signal not found", 404)
                
                return self.success_response(result[0])
                
            except Exception as e:
                logger.error(f"Error getting signal {signal_id}: {e}")
                return self.error_response(f"Failed to get signal: {str(e)}", 500)
        
        @self.blueprint.route('/stats', methods=['GET'])
        def get_signals_stats():
            """Get signals statistics"""
            try:
                # Get total signals
                total_signals = self.execute_scalar("SELECT COUNT(*) FROM signals")
                
                # Get signals by type
                signal_types = self.execute_query("""
                    SELECT signal_type, COUNT(*) as count 
                    FROM signals 
                    GROUP BY signal_type 
                    ORDER BY count DESC
                """)
                
                # Get today's signals
                today = datetime.now().date()
                today_signals = self.execute_scalar("""
                    SELECT COUNT(*) FROM signals WHERE DATE(ts) = :today
                """, {'today': today})
                
                # Get yesterday's signals
                yesterday = today - timedelta(days=1)
                yesterday_signals = self.execute_scalar("""
                    SELECT COUNT(*) FROM signals WHERE DATE(ts) = :yesterday
                """, {'yesterday': yesterday})
                
                stats = {
                    'total_signals': total_signals,
                    'today_signals': today_signals,
                    'yesterday_signals': yesterday_signals,
                    'signals_change': today_signals - yesterday_signals,
                    'signal_types': signal_types
                }
                
                return self.success_response(stats)
                
            except Exception as e:
                logger.error(f"Error getting signals stats: {e}")
                return self.error_response(f"Failed to get signals stats: {str(e)}", 500)

# Create the API instance
signals_api = SignalsAPI()