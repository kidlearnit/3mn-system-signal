#!/usr/bin/env python3
"""
Strategies REST API endpoints
"""

from flask import request
from .base_api import BaseAPI
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class StrategiesAPI(BaseAPI):
    """Strategies REST API"""
    
    def __init__(self):
        super().__init__('strategies', '/api/v1/strategies')
        self._register_routes()
    
    def _register_routes(self):
        """Register strategies routes"""
        
        @self.blueprint.route('', methods=['GET'])
        def get_strategies():
            """Get all strategies with pagination and filtering"""
            try:
                page, per_page = self.validate_pagination_params()
                
                # Build base query
                query = """
                    SELECT st.id, st.name, st.description, st.active,
                           COUNT(DISTINCT sig.id) as signal_count,
                           st.created_at
                    FROM trade_strategies st
                    LEFT JOIN signals sig ON st.id = sig.strategy_id
                """
                
                # Build filter conditions
                allowed_filters = ['active']
                conditions, params = self.build_filter_conditions(allowed_filters)
                
                # Add search filter
                search = request.args.get('search')
                if search:
                    conditions.append("(st.name LIKE :search OR st.description LIKE :search)")
                    params['search'] = f'%{search}%'
                
                # Add WHERE clause if conditions exist
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                # Add GROUP BY and ORDER BY
                query += " GROUP BY st.id ORDER BY st.name ASC"
                
                # Get paginated results
                result = self.paginate_query(query, params, page, per_page)
                return self.success_response(result)
                
            except Exception as e:
                logger.error(f"Error getting strategies: {e}")
                return self.error_response(f"Failed to get strategies: {str(e)}", 500)
        
        @self.blueprint.route('/<int:strategy_id>', methods=['GET'])
        def get_strategy(strategy_id):
            """Get strategy by ID"""
            try:
                query = """
                    SELECT st.id, st.name, st.description, st.active,
                           COUNT(DISTINCT sig.id) as signal_count,
                           st.created_at
                    FROM trade_strategies st
                    LEFT JOIN signals sig ON st.id = sig.strategy_id
                    WHERE st.id = :strategy_id
                    GROUP BY st.id
                """
                
                result = self.execute_query(query, {'strategy_id': strategy_id})
                
                if not result:
                    return self.error_response("Strategy not found", 404)
                
                return self.success_response(result[0])
                
            except Exception as e:
                logger.error(f"Error getting strategy {strategy_id}: {e}")
                return self.error_response(f"Failed to get strategy: {str(e)}", 500)
        
        @self.blueprint.route('', methods=['POST'])
        def create_strategy():
            """Create new strategy"""
            try:
                data = request.get_json()
                
                # Validate required fields
                if not data.get('name'):
                    return self.error_response("Missing required field: name", 400)
                
                # Check if strategy already exists
                existing = self.execute_scalar(
                    "SELECT COUNT(*) FROM trade_strategies WHERE name = :name",
                    {'name': data['name']}
                )
                
                if existing > 0:
                    return self.error_response("Strategy already exists", 409)
                
                # Insert new strategy
                insert_query = """
                    INSERT INTO trade_strategies (name, description, active)
                    VALUES (:name, :description, :active)
                """
                
                params = {
                    'name': data['name'],
                    'description': data.get('description', ''),
                    'active': data.get('active', True)
                }
                
                with self.engine.connect() as connection:
                    result = connection.execute(self.engine.text(insert_query), params)
                    connection.commit()
                    strategy_id = result.lastrowid
                
                # Return created strategy
                return self.get_strategy(strategy_id)
                
            except Exception as e:
                logger.error(f"Error creating strategy: {e}")
                return self.error_response(f"Failed to create strategy: {str(e)}", 500)
        
        @self.blueprint.route('/<int:strategy_id>', methods=['PUT'])
        def update_strategy(strategy_id):
            """Update strategy"""
            try:
                data = request.get_json()
                
                # Check if strategy exists
                existing = self.execute_scalar(
                    "SELECT COUNT(*) FROM trade_strategies WHERE id = :strategy_id",
                    {'strategy_id': strategy_id}
                )
                
                if existing == 0:
                    return self.error_response("Strategy not found", 404)
                
                # Build update query
                update_fields = []
                params = {'strategy_id': strategy_id}
                
                allowed_fields = ['name', 'description', 'active']
                for field in allowed_fields:
                    if field in data:
                        update_fields.append(f"{field} = :{field}")
                        params[field] = data[field]
                
                if not update_fields:
                    return self.error_response("No fields to update", 400)
                
                update_query = f"""
                    UPDATE trade_strategies 
                    SET {', '.join(update_fields)}
                    WHERE id = :strategy_id
                """
                
                with self.engine.connect() as connection:
                    connection.execute(self.engine.text(update_query), params)
                    connection.commit()
                
                # Return updated strategy
                return self.get_strategy(strategy_id)
                
            except Exception as e:
                logger.error(f"Error updating strategy {strategy_id}: {e}")
                return self.error_response(f"Failed to update strategy: {str(e)}", 500)
        
        @self.blueprint.route('/<int:strategy_id>', methods=['DELETE'])
        def delete_strategy(strategy_id):
            """Delete strategy"""
            try:
                # Check if strategy exists
                existing = self.execute_scalar(
                    "SELECT COUNT(*) FROM trade_strategies WHERE id = :strategy_id",
                    {'strategy_id': strategy_id}
                )
                
                if existing == 0:
                    return self.error_response("Strategy not found", 404)
                
                # Check if strategy has signals
                signal_count = self.execute_scalar(
                    "SELECT COUNT(*) FROM signals WHERE strategy_id = :strategy_id",
                    {'strategy_id': strategy_id}
                )
                
                if signal_count > 0:
                    return self.error_response("Cannot delete strategy with existing signals", 409)
                
                # Delete strategy
                delete_query = "DELETE FROM trade_strategies WHERE id = :strategy_id"
                
                with self.engine.connect() as connection:
                    connection.execute(self.engine.text(delete_query), {'strategy_id': strategy_id})
                    connection.commit()
                
                return self.success_response(message="Strategy deleted successfully")
                
            except Exception as e:
                logger.error(f"Error deleting strategy {strategy_id}: {e}")
                return self.error_response(f"Failed to delete strategy: {str(e)}", 500)
        
        @self.blueprint.route('/stats', methods=['GET'])
        def get_strategies_stats():
            """Get strategies statistics"""
            try:
                # Get total strategies
                total_strategies = self.execute_scalar("SELECT COUNT(*) FROM trade_strategies")
                
                # Get active strategies
                active_strategies = self.execute_scalar("SELECT COUNT(*) FROM trade_strategies WHERE active = 1")
                
                # Get inactive strategies
                inactive_strategies = self.execute_scalar("SELECT COUNT(*) FROM trade_strategies WHERE active = 0")
                
                # Get strategies with signals
                strategies_with_signals = self.execute_scalar("""
                    SELECT COUNT(DISTINCT strategy_id) FROM signals
                """)
                
                # Get top strategies by signal count
                top_strategies = self.execute_query("""
                    SELECT st.name, COUNT(s.id) as signal_count
                    FROM trade_strategies st
                    LEFT JOIN signals s ON st.id = s.strategy_id
                    GROUP BY st.id, st.name
                    ORDER BY signal_count DESC
                    LIMIT 10
                """)
                
                stats = {
                    'total_strategies': total_strategies,
                    'active_strategies': active_strategies,
                    'inactive_strategies': inactive_strategies,
                    'strategies_with_signals': strategies_with_signals,
                    'top_strategies': top_strategies
                }
                
                return self.success_response(stats)
                
            except Exception as e:
                logger.error(f"Error getting strategies stats: {e}")
                return self.error_response(f"Failed to get strategies stats: {str(e)}", 500)
        
        @self.blueprint.route('/<int:strategy_id>/signals', methods=['GET'])
        def get_strategy_signals(strategy_id):
            """Get signals for a specific strategy"""
            try:
                page, per_page = self.validate_pagination_params()
                
                # Check if strategy exists
                strategy_exists = self.execute_scalar(
                    "SELECT COUNT(*) FROM trade_strategies WHERE id = :strategy_id",
                    {'strategy_id': strategy_id}
                )
                
                if strategy_exists == 0:
                    return self.error_response("Strategy not found", 404)
                
                # Build query for signals
                query = """
                    SELECT s.id, s.symbol_id, s.timeframe, s.ts, s.signal_type, s.details,
                           sym.ticker, sym.exchange
                    FROM signals s
                    JOIN symbols sym ON s.symbol_id = sym.id
                    WHERE s.strategy_id = :strategy_id
                """
                
                params = {'strategy_id': strategy_id}
                
                # Add filters
                allowed_filters = ['signal_type', 'timeframe', 'symbol_id']
                conditions, filter_params = self.build_filter_conditions(allowed_filters)
                
                if conditions:
                    query += " AND " + " AND ".join(conditions)
                    params.update(filter_params)
                
                query += " ORDER BY s.ts DESC"
                
                # Get paginated results
                result = self.paginate_query(query, params, page, per_page)
                return self.success_response(result)
                
            except Exception as e:
                logger.error(f"Error getting signals for strategy {strategy_id}: {e}")
                return self.error_response(f"Failed to get strategy signals: {str(e)}", 500)

# Create the API instance
strategies_api = StrategiesAPI()
