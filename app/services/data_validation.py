import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pymysql
import logging

logger = logging.getLogger(__name__)

class DataValidator:
    """Data validation service for workflow execution"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv("MYSQL_HOST", "mysql"),
            'port': int(os.getenv("MYSQL_PORT", 3306)),
            'user': os.getenv("MYSQL_USER", "trader"),
            'password': os.getenv("MYSQL_PASSWORD", "traderpass"),
            'database': os.getenv("MYSQL_DB", "trading"),
        }
    
    def _get_db_connection(self):
        """Get database connection"""
        return pymysql.connect(**self.db_config, autocommit=True)
    
    def validate_execution_environment(self) -> Dict:
        """Validate if the execution environment is ready"""
        env_status = {
            'environment_valid': True,
            'database_connected': False,
            'redis_connected': False,
            'messages': []
        }
        
        # Check Database connection
        try:
            conn = self._get_db_connection()
            conn.close()
            env_status['database_connected'] = True
            env_status['messages'].append("Database connection successful.")
        except Exception as e:
            env_status['environment_valid'] = False
            env_status['messages'].append(f"Database connection failed: {str(e)}")

        # Placeholder for Redis check
        env_status['redis_connected'] = True
        env_status['messages'].append("Redis connection assumed successful (placeholder).")

        return env_status

    def validate_workflow_data_requirements(self, nodes: list) -> Dict:
        """Validate if the workflow has the necessary data"""
        workflow_status = {
            'workflow_valid': True,
            'data_checks': []
        }

        # Extract symbols and timeframes from nodes
        required_symbols = set()
        required_timeframes = set()
        for node in nodes:
            if node['type'] == 'symbol':
                props = node.get('properties', {})
                ticker = props.get('ticker')
                exchange = props.get('exchange')
                tfs = props.get('timeframes', [])
                if ticker and exchange:
                    required_symbols.add((ticker, exchange))
                for tf in tfs:
                    required_timeframes.add(tf)
        
        if not required_symbols:
            workflow_status['workflow_valid'] = False
            workflow_status['data_checks'].append({'type': 'error', 'message': 'No symbol nodes found in workflow.'})
            return workflow_status

        # Check each required symbol's data freshness and completeness
        for ticker, exchange in required_symbols:
            try:
                conn = self._get_db_connection()
                try:
                    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                        cursor.execute("SELECT id FROM symbols WHERE ticker = %s AND exchange = %s", (ticker, exchange))
                        symbol_result = cursor.fetchone()
                        if not symbol_result:
                            workflow_status['workflow_valid'] = False
                            workflow_status['data_checks'].append({'type': 'error', 'message': f'Symbol {ticker} ({exchange}) not found in database.'})
                            continue
                        symbol_id = symbol_result['id']

                        for tf in required_timeframes:
                            check_result = self._check_symbol_timeframe_data(cursor, symbol_id, ticker, tf)
                            workflow_status['data_checks'].append(check_result)
                            if not check_result['is_valid']:
                                workflow_status['workflow_valid'] = False
                finally:
                    conn.close()
            except Exception as e:
                workflow_status['workflow_valid'] = False
                workflow_status['data_checks'].append({'type': 'error', 'message': f'Error checking {ticker}: {str(e)}'})
        
        return workflow_status

    def _check_symbol_timeframe_data(self, cursor, symbol_id: int, ticker: str, timeframe: str) -> Dict:
        """Check data freshness and completeness for a specific symbol and timeframe"""
        check_info = {
            'symbol': ticker,
            'timeframe': timeframe,
            'is_valid': True,
            'messages': []
        }

        # Check data freshness (e.g., last update within 5 minutes for 1m data)
        freshness_threshold = datetime.utcnow() - timedelta(minutes=5)
        
        # Get latest candle
        cursor.execute("""
            SELECT ts, close FROM candles_tf 
            WHERE symbol_id = %s AND timeframe = %s
            ORDER BY ts DESC LIMIT 1
        """, (symbol_id, timeframe))
        latest_candle = cursor.fetchone()

        if not latest_candle:
            check_info['is_valid'] = False
            check_info['messages'].append(f"No data found for {ticker} {timeframe}.")
        else:
            if latest_candle['ts'] < freshness_threshold:
                check_info['is_valid'] = False
                check_info['messages'].append(f"Data for {ticker} {timeframe} is stale (last update: {latest_candle['ts'].isoformat()}).")
            else:
                check_info['messages'].append(f"Data for {ticker} {timeframe} is fresh (last update: {latest_candle['ts'].isoformat()}).")
            
            # Check data completeness (e.g., enough candles for indicators)
            cursor.execute("""
                SELECT COUNT(*) as count FROM candles_tf 
                WHERE symbol_id = %s AND timeframe = %s
            """, (symbol_id, timeframe))
            candle_count = cursor.fetchone()['count']

            if candle_count < 100:
                check_info['is_valid'] = False
                check_info['messages'].append(f"Insufficient data for {ticker} {timeframe} ({candle_count} candles, 100 required).")
            else:
                check_info['messages'].append(f"Sufficient data for {ticker} {timeframe} ({candle_count} candles).")
            
            # Check data quality (e.g., no zero prices)
            if latest_candle['close'] <= 0:
                check_info['is_valid'] = False
                check_info['messages'].append(f"Data quality issue: Zero or negative close price for {ticker} {timeframe}.")
            else:
                check_info['messages'].append(f"Data quality for {ticker} {timeframe} is good.")

        return check_info

    def get_data_snapshot(self, symbol_id: int, timeframe: str, limit: int = 100) -> Dict:
        """Get a snapshot of recent data for a symbol and timeframe"""
        try:
            conn = self._get_db_connection()
            try:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute("""
                        SELECT ts, open, high, low, close, volume
                        FROM candles_tf 
                        WHERE symbol_id = %s AND timeframe = %s
                        ORDER BY ts DESC 
                        LIMIT %s
                    """, (symbol_id, timeframe, limit))
                    result = cursor.fetchall()
                    
                    candles = []
                    for row in result:
                        candles.append({
                            'timestamp': row['ts'].isoformat(),
                            'open': float(row['open']),
                            'high': float(row['high']),
                            'low': float(row['low']),
                            'close': float(row['close']),
                            'volume': float(row['volume']) if row['volume'] else 0
                        })
                    
                    return {'symbol_id': symbol_id, 'timeframe': timeframe, 'data': candles[::-1]}
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Error getting data snapshot: {e}")
            return {'symbol_id': symbol_id, 'timeframe': timeframe, 'data': [], 'error': str(e)}