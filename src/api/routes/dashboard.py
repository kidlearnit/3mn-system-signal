#!/usr/bin/env python3
"""
Dashboard REST API endpoints
"""

from flask import request
from .base_api import BaseAPI
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DashboardAPI(BaseAPI):
    """Dashboard REST API"""
    
    def __init__(self):
        super().__init__('dashboard', '/api/v1/dashboard')
        self._register_routes()
    
    def _register_routes(self):
        """Register dashboard routes"""
        
        @self.blueprint.route('/overview', methods=['GET'])
        def get_overview():
            """Get dashboard overview statistics"""
            try:
                total_symbols = self.execute_scalar("SELECT COUNT(*) FROM symbols")
                total_strategies = self.execute_scalar("SELECT COUNT(*) FROM trade_strategies")
                total_signals = self.execute_scalar("SELECT COUNT(*) FROM signals")
                
                overview = {
                    'symbols': {'total': total_symbols},
                    'strategies': {'total': total_strategies},
                    'signals': {'total': total_signals}
                }
                
                return self.success_response(overview)
                
            except Exception as e:
                logger.error(f"Error getting dashboard overview: {e}")
                return self.error_response(f"Failed to get dashboard overview: {str(e)}", 500)

# Create the API instance
dashboard_api = DashboardAPI()
