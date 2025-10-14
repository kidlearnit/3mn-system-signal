#!/usr/bin/env python3
"""
Symbols REST API endpoints
"""

from flask import request
from .base_api import BaseAPI
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SymbolsAPI(BaseAPI):
    """Symbols REST API"""
    
    def __init__(self):
        super().__init__('symbols', '/api/v1/symbols')
        self._register_routes()
    
    def _register_routes(self):
        """Register symbols routes"""
        
        @self.blueprint.route('', methods=['GET'])
        def get_symbols():
            """Get all symbols with pagination and filtering"""
            try:
                page, per_page = self.validate_pagination_params()
                
                # Build base query
                query = """
                    SELECT s.id, s.ticker, s.exchange, s.currency, s.active,
                           COUNT(DISTINCT sig.id) as signal_count
                    FROM symbols s
                    LEFT JOIN signals sig ON s.id = sig.symbol_id
                """
                
                # Build filter conditions
                allowed_filters = ['exchange', 'currency', 'active']
                conditions, params = self.build_filter_conditions(allowed_filters)
                
                # Add search filter
                search = request.args.get('search')
                if search:
                    conditions.append("(s.ticker LIKE :search OR s.exchange LIKE :search)")
                    params['search'] = f'%{search}%'
                
                # Add WHERE clause if conditions exist
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                # Add GROUP BY and ORDER BY
                query += " GROUP BY s.id ORDER BY s.ticker ASC"
                
                # Get paginated results
                result = self.paginate_query(query, params, page, per_page)
                return self.success_response(result)
                
            except Exception as e:
                logger.error(f"Error getting symbols: {e}")
                return self.error_response(f"Failed to get symbols: {str(e)}", 500)
        
        @self.blueprint.route('/<int:symbol_id>', methods=['GET'])
        def get_symbol(symbol_id):
            """Get symbol by ID"""
            try:
                query = """
                    SELECT s.id, s.ticker, s.exchange, s.currency, s.active,
                           COUNT(DISTINCT sig.id) as signal_count,
                           s.created_at
                    FROM symbols s
                    LEFT JOIN signals sig ON s.id = sig.symbol_id
                    WHERE s.id = :symbol_id
                    GROUP BY s.id
                """
                
                result = self.execute_query(query, {'symbol_id': symbol_id})
                
                if not result:
                    return self.error_response("Symbol not found", 404)
                
                return self.success_response(result[0])
                
            except Exception as e:
                logger.error(f"Error getting symbol {symbol_id}: {e}")
                return self.error_response(f"Failed to get symbol: {str(e)}", 500)
        
        @self.blueprint.route('', methods=['POST'])
        def create_symbol():
            """Create new symbol"""
            try:
                data = request.get_json()
                
                # Validate required fields
                required_fields = ['ticker', 'exchange']
                for field in required_fields:
                    if not data.get(field):
                        return self.error_response(f"Missing required field: {field}", 400)
                
                # Check if symbol already exists
                existing = self.execute_scalar(
                    "SELECT COUNT(*) FROM symbols WHERE ticker = :ticker",
                    {'ticker': data['ticker']}
                )
                
                if existing > 0:
                    return self.error_response("Symbol already exists", 409)
                
                # Insert new symbol
                insert_query = """
                    INSERT INTO symbols (ticker, exchange, currency, active)
                    VALUES (:ticker, :exchange, :currency, :active)
                """
                
                params = {
                    'ticker': data['ticker'],
                    'exchange': data['exchange'],
                    'currency': data.get('currency', 'USD'),
                    'active': data.get('active', True)
                }
                
                with self.engine.connect() as connection:
                    result = connection.execute(self.engine.text(insert_query), params)
                    connection.commit()
                    symbol_id = result.lastrowid
                
                # Return created symbol
                return self.get_symbol(symbol_id)
                
            except Exception as e:
                logger.error(f"Error creating symbol: {e}")
                return self.error_response(f"Failed to create symbol: {str(e)}", 500)
        
        @self.blueprint.route('/<int:symbol_id>', methods=['PUT'])
        def update_symbol(symbol_id):
            """Update symbol"""
            try:
                data = request.get_json()
                
                # Check if symbol exists
                existing = self.execute_scalar(
                    "SELECT COUNT(*) FROM symbols WHERE id = :symbol_id",
                    {'symbol_id': symbol_id}
                )
                
                if existing == 0:
                    return self.error_response("Symbol not found", 404)
                
                # Build update query
                update_fields = []
                params = {'symbol_id': symbol_id}
                
                allowed_fields = ['ticker', 'exchange', 'currency', 'active']
                for field in allowed_fields:
                    if field in data:
                        update_fields.append(f"{field} = :{field}")
                        params[field] = data[field]
                
                if not update_fields:
                    return self.error_response("No fields to update", 400)
                
                update_query = f"""
                    UPDATE symbols 
                    SET {', '.join(update_fields)}
                    WHERE id = :symbol_id
                """
                
                with self.engine.connect() as connection:
                    connection.execute(self.engine.text(update_query), params)
                    connection.commit()
                
                # Return updated symbol
                return self.get_symbol(symbol_id)
                
            except Exception as e:
                logger.error(f"Error updating symbol {symbol_id}: {e}")
                return self.error_response(f"Failed to update symbol: {str(e)}", 500)
        
        @self.blueprint.route('/<int:symbol_id>', methods=['DELETE'])
        def delete_symbol(symbol_id):
            """Delete symbol"""
            try:
                # Check if symbol exists
                existing = self.execute_scalar(
                    "SELECT COUNT(*) FROM symbols WHERE id = :symbol_id",
                    {'symbol_id': symbol_id}
                )
                
                if existing == 0:
                    return self.error_response("Symbol not found", 404)
                
                # Check if symbol has signals
                signal_count = self.execute_scalar(
                    "SELECT COUNT(*) FROM signals WHERE symbol_id = :symbol_id",
                    {'symbol_id': symbol_id}
                )
                
                if signal_count > 0:
                    return self.error_response("Cannot delete symbol with existing signals", 409)
                
                # Delete symbol
                delete_query = "DELETE FROM symbols WHERE id = :symbol_id"
                
                with self.engine.connect() as connection:
                    connection.execute(self.engine.text(delete_query), {'symbol_id': symbol_id})
                    connection.commit()
                
                return self.success_response(message="Symbol deleted successfully")
                
            except Exception as e:
                logger.error(f"Error deleting symbol {symbol_id}: {e}")
                return self.error_response(f"Failed to delete symbol: {str(e)}", 500)
        
        @self.blueprint.route('/stats', methods=['GET'])
        def get_symbols_stats():
            """Get symbols statistics"""
            try:
                # Get total symbols
                total_symbols = self.execute_scalar("SELECT COUNT(*) FROM symbols")
                
                # Get active symbols
                active_symbols = self.execute_scalar("SELECT COUNT(*) FROM symbols WHERE active = 1")
                
                # Get inactive symbols
                inactive_symbols = self.execute_scalar("SELECT COUNT(*) FROM symbols WHERE active = 0")
                
                # Get symbols by exchange
                exchanges = self.execute_query("""
                    SELECT exchange, COUNT(*) as count 
                    FROM symbols 
                    GROUP BY exchange 
                    ORDER BY count DESC
                """)
                
                # Get symbols with signals
                symbols_with_signals = self.execute_scalar("""
                    SELECT COUNT(DISTINCT symbol_id) FROM signals
                """)
                
                stats = {
                    'total_symbols': total_symbols,
                    'active_symbols': active_symbols,
                    'inactive_symbols': inactive_symbols,
                    'symbols_with_signals': symbols_with_signals,
                    'exchanges': exchanges
                }
                
                return self.success_response(stats)
                
            except Exception as e:
                logger.error(f"Error getting symbols stats: {e}")
                return self.error_response(f"Failed to get symbols stats: {str(e)}", 500)
        
        @self.blueprint.route('/<int:symbol_id>/signals', methods=['GET'])
        def get_symbol_signals(symbol_id):
            """Get signals for a specific symbol"""
            try:
                page, per_page = self.validate_pagination_params()
                
                # Check if symbol exists
                symbol_exists = self.execute_scalar(
                    "SELECT COUNT(*) FROM symbols WHERE id = :symbol_id",
                    {'symbol_id': symbol_id}
                )
                
                if symbol_exists == 0:
                    return self.error_response("Symbol not found", 404)
                
                # Build query for signals
                query = """
                    SELECT s.id, s.signal_type, s.timeframe, s.ts, s.strategy_id,
                           st.name as strategy_name, s.details
                    FROM signals s
                    JOIN trade_strategies st ON s.strategy_id = st.id
                    WHERE s.symbol_id = :symbol_id
                """
                
                params = {'symbol_id': symbol_id}
                
                # Add filters
                allowed_filters = ['signal_type', 'timeframe', 'strategy_id']
                conditions, filter_params = self.build_filter_conditions(allowed_filters)
                
                if conditions:
                    query += " AND " + " AND ".join(conditions)
                    params.update(filter_params)
                
                query += " ORDER BY s.ts DESC"
                
                # Get paginated results
                result = self.paginate_query(query, params, page, per_page)
                return self.success_response(result)
                
            except Exception as e:
                logger.error(f"Error getting signals for symbol {symbol_id}: {e}")
                return self.error_response(f"Failed to get symbol signals: {str(e)}", 500)

# Create the API instance
symbols_api = SymbolsAPI()
