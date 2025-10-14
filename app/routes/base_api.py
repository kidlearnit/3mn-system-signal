#!/usr/bin/env python3
"""
Base API class for REST endpoints
"""

from flask import Blueprint, jsonify, request
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseAPI:
    """Base class for REST API endpoints"""
    
    def __init__(self, blueprint_name: str, url_prefix: str = ''):
        self.blueprint = Blueprint(blueprint_name, __name__, url_prefix=url_prefix)
        self.engine = None
        self.SessionLocal = None
        # Database will be initialized when first used
        # Routes will be registered by subclasses
    
    def _init_db(self):
        """Initialize database connection"""
        try:
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                logger.warning("DATABASE_URL environment variable not set, database connection will be initialized later")
                return
            
            self.engine = create_engine(database_url, pool_pre_ping=True, pool_recycle=3600)
            self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
            logger.info("Database connection initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def _register_routes(self):
        """Register routes - to be implemented by subclasses"""
        pass
    
    def get_db_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute raw SQL query and return results as list of dicts"""
        try:
            if self.engine is None:
                self._init_db()
            with self.engine.connect() as connection:
                result = connection.execute(text(query), params or {})
                columns = result.keys()
                return [dict(zip(columns, row)) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
    
    def execute_scalar(self, query: str, params: Dict = None) -> Any:
        """Execute query and return scalar result"""
        try:
            if self.engine is None:
                self._init_db()
            with self.engine.connect() as connection:
                result = connection.execute(text(query), params or {})
                return result.scalar()
        except Exception as e:
            logger.error(f"Scalar query execution error: {e}")
            raise
    
    def success_response(self, data: Any = None, message: str = "Success", status_code: int = 200):
        """Create success response"""
        response = {
            "success": True,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        if data is not None:
            response["data"] = data
        return jsonify(response), status_code
    
    def error_response(self, message: str = "Error", status_code: int = 400, details: Any = None):
        """Create error response"""
        response = {
            "success": False,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        if details is not None:
            response["details"] = details
        return jsonify(response), status_code
    
    def paginate_query(self, query: str, params: Dict = None, page: int = 1, per_page: int = 20) -> Dict:
        """Paginate query results"""
        try:
            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM ({query}) as count_query"
            total = self.execute_scalar(count_query, params)
            
            # Calculate pagination
            offset = (page - 1) * per_page
            paginated_query = f"{query} LIMIT {per_page} OFFSET {offset}"
            
            # Get paginated results
            results = self.execute_query(paginated_query, params)
            
            # Calculate pagination info
            total_pages = (total + per_page - 1) // per_page
            
            return {
                "items": results,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
        except Exception as e:
            logger.error(f"Pagination error: {e}")
            raise
    
    def validate_pagination_params(self) -> tuple:
        """Validate and return pagination parameters"""
        try:
            page = max(1, int(request.args.get('page', 1)))
            per_page = min(100, max(1, int(request.args.get('per_page', 20))))
            return page, per_page
        except (ValueError, TypeError):
            return 1, 20
    
    def build_filter_conditions(self, allowed_filters: List[str]) -> tuple:
        """Build WHERE conditions and parameters from request args"""
        conditions = []
        params = {}
        param_count = 0
        
        for filter_name in allowed_filters:
            value = request.args.get(filter_name)
            if value:
                param_count += 1
                param_name = f"{filter_name}_{param_count}"
                conditions.append(f"{filter_name} = :{param_name}")
                params[param_name] = value
        
        return conditions, params
