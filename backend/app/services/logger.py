#!/usr/bin/env python3
"""
Centralized Logging Service
"""

import os
import logging
import traceback
from datetime import datetime
from typing import Optional

class TradingLogger:
    """Centralized logger for trading system"""
    
    def __init__(self):
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if not exists
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                # File handler for errors
                logging.FileHandler(
                    os.path.join(log_dir, 'errors.log'),
                    mode='a',
                    encoding='utf-8'
                ),
                # File handler for all logs
                logging.FileHandler(
                    os.path.join(log_dir, 'system.log'),
                    mode='a',
                    encoding='utf-8'
                ),
                # Console handler
                logging.StreamHandler()
            ]
        )
        
        # Create specific loggers
        self.error_logger = logging.getLogger('trading.errors')
        self.system_logger = logging.getLogger('trading.system')
        self.backfill_logger = logging.getLogger('trading.backfill')
        self.scheduler_logger = logging.getLogger('trading.scheduler')
        self.worker_logger = logging.getLogger('trading.worker')
        
        # Set levels
        self.error_logger.setLevel(logging.ERROR)
        self.system_logger.setLevel(logging.INFO)
        self.backfill_logger.setLevel(logging.INFO)
        self.scheduler_logger.setLevel(logging.INFO)
        self.worker_logger.setLevel(logging.INFO)
    
    def log_error(self, message: str, error: Optional[Exception] = None, context: Optional[dict] = None):
        """Log error with full context"""
        error_msg = f"ERROR: {message}"
        
        if context:
            error_msg += f" | Context: {context}"
        
        if error:
            error_msg += f" | Exception: {str(error)}"
            error_msg += f" | Traceback: {traceback.format_exc()}"
        
        self.error_logger.error(error_msg)
        print(f"❌ {error_msg}")  # Also print to console
    
    def log_backfill_error(self, symbol: str, exchange: str, error: Exception, context: Optional[dict] = None):
        """Log backfill specific errors"""
        error_msg = f"BACKFILL ERROR: {symbol} ({exchange})"
        
        if context:
            error_msg += f" | Context: {context}"
        
        error_msg += f" | Error: {str(error)}"
        error_msg += f" | Traceback: {traceback.format_exc()}"
        
        self.error_logger.error(error_msg)
        self.backfill_logger.error(error_msg)
        print(f"❌ {error_msg}")
    
    def log_scheduler_error(self, message: str, error: Optional[Exception] = None, context: Optional[dict] = None):
        """Log scheduler specific errors"""
        error_msg = f"SCHEDULER ERROR: {message}"
        
        if context:
            error_msg += f" | Context: {context}"
        
        if error:
            error_msg += f" | Error: {str(error)}"
            error_msg += f" | Traceback: {traceback.format_exc()}"
        
        self.error_logger.error(error_msg)
        self.scheduler_logger.error(error_msg)
        print(f"❌ {error_msg}")
    
    def log_worker_error(self, worker_name: str, job_id: str, error: Exception, context: Optional[dict] = None):
        """Log worker specific errors"""
        error_msg = f"WORKER ERROR: {worker_name} | Job: {job_id}"
        
        if context:
            error_msg += f" | Context: {context}"
        
        error_msg += f" | Error: {str(error)}"
        error_msg += f" | Traceback: {traceback.format_exc()}"
        
        self.error_logger.error(error_msg)
        self.worker_logger.error(error_msg)
        print(f"❌ {error_msg}")
    
    def log_system_info(self, message: str, context: Optional[dict] = None):
        """Log system information"""
        info_msg = f"SYSTEM: {message}"
        
        if context:
            info_msg += f" | Context: {context}"
        
        self.system_logger.info(info_msg)
        print(f"ℹ️ {info_msg}")
    
    def log_backfill_success(self, symbol: str, exchange: str, rows_count: int, context: Optional[dict] = None):
        """Log successful backfill"""
        success_msg = f"BACKFILL SUCCESS: {symbol} ({exchange}) | Rows: {rows_count}"
        
        if context:
            success_msg += f" | Context: {context}"
        
        self.backfill_logger.info(success_msg)
        print(f"✅ {success_msg}")
    
    def log_scheduler_info(self, message: str, context: Optional[dict] = None):
        """Log scheduler information"""
        info_msg = f"SCHEDULER: {message}"
        
        if context:
            info_msg += f" | Context: {context}"
        
        self.scheduler_logger.info(info_msg)
        print(f"🔄 {info_msg}")

# Global logger instance
trading_logger = TradingLogger()

# Convenience functions
def log_error(message: str, error: Optional[Exception] = None, context: Optional[dict] = None):
    """Log error"""
    trading_logger.log_error(message, error, context)

def log_backfill_error(symbol: str, exchange: str, error: Exception, context: Optional[dict] = None):
    """Log backfill error"""
    trading_logger.log_backfill_error(symbol, exchange, error, context)

def log_scheduler_error(message: str, error: Optional[Exception] = None, context: Optional[dict] = None):
    """Log scheduler error"""
    trading_logger.log_scheduler_error(message, error, context)

def log_worker_error(worker_name: str, job_id: str, error: Exception, context: Optional[dict] = None):
    """Log worker error"""
    trading_logger.log_worker_error(worker_name, job_id, error, context)

def log_system_info(message: str, context: Optional[dict] = None):
    """Log system info"""
    trading_logger.log_system_info(message, context)

def log_backfill_success(symbol: str, exchange: str, rows_count: int, context: Optional[dict] = None):
    """Log backfill success"""
    trading_logger.log_backfill_success(symbol, exchange, rows_count, context)

def log_scheduler_info(message: str, context: Optional[dict] = None):
    """Log scheduler info"""
    trading_logger.log_scheduler_info(message, context)
