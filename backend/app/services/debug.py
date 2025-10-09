import os
import logging
import traceback
import datetime as dt
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from ..db import SessionLocal

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DebugHelper:
    """Helper class for debugging trading signals system"""
    
    def __init__(self):
        self.debug_log = []
    
    def log_step(self, step: str, data: Any = None, error: Exception = None):
        """Log a debugging step with optional data and error"""
        timestamp = dt.datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'step': step,
            'data': str(data) if data is not None else None,
            'error': str(error) if error else None,
            'traceback': traceback.format_exc() if error else None
        }
        self.debug_log.append(log_entry)
        
        if error:
            logger.error(f"[{timestamp}] {step}: {error}")
        else:
            logger.info(f"[{timestamp}] {step}: {data}")
    
    def get_debug_log(self) -> List[Dict]:
        """Get the complete debug log"""
        return self.debug_log
    
    def clear_log(self):
        """Clear the debug log"""
        self.debug_log = []

# Global debug helper instance
debug_helper = DebugHelper()

def debug_database_connection():
    """Debug database connection"""
    try:
        debug_helper.log_step("Testing database connection")
        with SessionLocal() as s:
            result = s.execute(text("SELECT 1 as test")).scalar()
            debug_helper.log_step("Database connection successful", f"Test query result: {result}")
            return True
    except Exception as e:
        debug_helper.log_step("Database connection failed", error=e)
        return False

def debug_symbols_table():
    """Debug symbols table"""
    try:
        debug_helper.log_step("Checking symbols table")
        with SessionLocal() as s:
            # Check table exists
            result = s.execute(text("SHOW TABLES LIKE 'symbols'")).fetchall()
            debug_helper.log_step("Symbols table check", f"Table exists: {len(result) > 0}")
            
            if len(result) > 0:
                # Get active symbols count
                count = s.execute(text("SELECT COUNT(*) FROM symbols WHERE active=1")).scalar()
                debug_helper.log_step("Active symbols count", count)
                
                # Get sample symbols
                symbols = s.execute(text("SELECT id, ticker, exchange FROM symbols WHERE active=1 LIMIT 5")).fetchall()
                debug_helper.log_step("Sample active symbols", [dict(s._mapping) for s in symbols])
            
            return True
    except Exception as e:
        debug_helper.log_step("Symbols table debug failed", error=e)
        return False

def debug_data_sources():
    """Debug data source configurations"""
    try:
        debug_helper.log_step("Checking data source configurations")
        
        # Check environment variables
        env_vars = {
            'POLYGON_API_KEY': bool(os.getenv("POLYGON_API_KEY")),
            'VNSTOCK_ENABLED': os.getenv("VNSTOCK_ENABLED", "true"),
            'YF_ENABLED': os.getenv("YF_ENABLED", "true"),
            'DATABASE_URL': bool(os.getenv("DATABASE_URL")),
            'REDIS_URL': bool(os.getenv("REDIS_URL"))
        }
        debug_helper.log_step("Environment variables", env_vars)
        
        # Check vnstock import
        try:
            from vnstock import Quote
            debug_helper.log_step("vnstock import", "Success")
        except ImportError as e:
            debug_helper.log_step("vnstock import", "Failed", e)
        
        # Check yfinance import
        try:
            import yfinance as yf
            debug_helper.log_step("yfinance import", "Success")
        except ImportError as e:
            debug_helper.log_step("yfinance import", "Failed", e)
        
        return True
    except Exception as e:
        debug_helper.log_step("Data sources debug failed", error=e)
        return False

def debug_single_symbol(symbol_id: int, ticker: str, exchange: str):
    """Debug a single symbol processing"""
    try:
        debug_helper.log_step(f"Starting debug for {ticker} ({exchange})")
        
        # Check symbol in database
        with SessionLocal() as s:
            symbol_data = s.execute(text("""
                SELECT id, ticker, exchange, currency, active 
                FROM symbols WHERE id=:id
            """), {'id': symbol_id}).mappings().first()
            
            if symbol_data:
                debug_helper.log_step(f"Symbol data for {ticker}", dict(symbol_data))
            else:
                debug_helper.log_step(f"Symbol not found in database", f"ID: {symbol_id}")
                return False
        
        # Check existing candles
        with SessionLocal() as s:
            candle_count = s.execute(text("""
                SELECT COUNT(*) FROM candles_1m WHERE symbol_id=:id
            """), {'id': symbol_id}).scalar()
            debug_helper.log_step(f"Existing 1m candles for {ticker}", candle_count)
        
        # Check existing MACD data
        with SessionLocal() as s:
            macd_count = s.execute(text("""
                SELECT COUNT(*) FROM indicators_macd WHERE symbol_id=:id
            """), {'id': symbol_id}).scalar()
            debug_helper.log_step(f"Existing MACD data for {ticker}", macd_count)
        
        return True
    except Exception as e:
        debug_helper.log_step(f"Single symbol debug failed for {ticker}", error=e)
        return False

def debug_data_fetch(ticker: str, exchange: str, source: str = "auto"):
    """Debug data fetching for a specific ticker"""
    try:
        debug_helper.log_step(f"Testing data fetch for {ticker} from {source}")
        
        # Import data sources
        from .data_sources import backfill_1m
        
        # Test data fetch
        result = backfill_1m(999999, ticker, exchange, source=source)
        debug_helper.log_step(f"Data fetch result for {ticker}", f"Rows inserted: {result}")
        
        return result > 0
    except Exception as e:
        debug_helper.log_step(f"Data fetch debug failed for {ticker}", error=e)
        return False

def debug_thresholds():
    """Debug threshold configuration"""
    try:
        debug_helper.log_step("Checking threshold configuration")
        
        with SessionLocal() as s:
            # Check strategies
            strategies = s.execute(text("SELECT * FROM trade_strategies")).fetchall()
            debug_helper.log_step("Trade strategies", [dict(s._mapping) for s in strategies])
            
            # Check timeframes
            timeframes = s.execute(text("SELECT * FROM timeframes")).fetchall()
            debug_helper.log_step("Timeframes", [dict(s._mapping) for s in timeframes])
            
            # Check indicators
            indicators = s.execute(text("SELECT * FROM indicators")).fetchall()
            debug_helper.log_step("Indicators", [dict(s._mapping) for s in indicators])
            
            # Check zones
            zones = s.execute(text("SELECT * FROM zones")).fetchall()
            debug_helper.log_step("Zones", [dict(s._mapping) for s in zones])
            
            # Check threshold values
            threshold_count = s.execute(text("SELECT COUNT(*) FROM threshold_values")).scalar()
            debug_helper.log_step("Threshold values count", threshold_count)
        
        return True
    except Exception as e:
        debug_helper.log_step("Thresholds debug failed", error=e)
        return False

def debug_redis_connection():
    """Debug Redis connection"""
    try:
        debug_helper.log_step("Testing Redis connection")
        
        import redis
        r = redis.from_url(os.getenv('REDIS_URL'))
        
        # Test connection
        r.ping()
        debug_helper.log_step("Redis connection", "Success")
        
        # Check queue
        from rq import Queue
        q = Queue('default', connection=r)
        queue_length = len(q)
        debug_helper.log_step("Redis queue length", queue_length)
        
        return True
    except Exception as e:
        debug_helper.log_step("Redis connection failed", error=e)
        return False

def debug_full_system():
    """Run complete system debug"""
    debug_helper.clear_log()
    debug_helper.log_step("Starting full system debug")
    
    results = {
        'database': debug_database_connection(),
        'symbols': debug_symbols_table(),
        'data_sources': debug_data_sources(),
        'thresholds': debug_thresholds(),
        'redis': debug_redis_connection()
    }
    
    debug_helper.log_step("Full system debug completed", results)
    return results

def debug_symbol_pipeline(symbol_id: int, ticker: str, exchange: str):
    """Debug complete pipeline for a single symbol"""
    debug_helper.clear_log()
    debug_helper.log_step(f"Starting pipeline debug for {ticker}")
    
    results = {
        'symbol_check': debug_single_symbol(symbol_id, ticker, exchange),
        'data_fetch': debug_data_fetch(ticker, exchange),
        'thresholds': debug_thresholds()
    }
    
    debug_helper.log_step(f"Pipeline debug completed for {ticker}", results)
    return results

def get_debug_summary():
    """Get a summary of debug information"""
    log = debug_helper.get_debug_log()
    
    summary = {
        'total_steps': len(log),
        'errors': len([entry for entry in log if entry['error']]),
        'successful_steps': len([entry for entry in log if not entry['error']]),
        'last_error': None,
        'recent_steps': log[-10:] if log else []
    }
    
    # Find last error
    for entry in reversed(log):
        if entry['error']:
            summary['last_error'] = entry
            break
    
    return summary

def print_debug_log():
    """Print the complete debug log"""
    log = debug_helper.get_debug_log()
    
    print("\n" + "="*80)
    print("DEBUG LOG")
    print("="*80)
    
    for entry in log:
        print(f"\n[{entry['timestamp']}] {entry['step']}")
        if entry['data']:
            print(f"  Data: {entry['data']}")
        if entry['error']:
            print(f"  ERROR: {entry['error']}")
            if entry['traceback']:
                print(f"  Traceback:\n{entry['traceback']}")
    
    print("\n" + "="*80)
    print("DEBUG SUMMARY")
    print("="*80)
    
    summary = get_debug_summary()
    print(f"Total steps: {summary['total_steps']}")
    print(f"Errors: {summary['errors']}")
    print(f"Successful: {summary['successful_steps']}")
    
    if summary['last_error']:
        print(f"\nLast error: {summary['last_error']['step']}")
        print(f"Error message: {summary['last_error']['error']}")
