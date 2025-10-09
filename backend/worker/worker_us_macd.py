import os
import json
from sqlalchemy import text

# Import DB và init
from app.db import init_db
init_db(os.getenv("DATABASE_URL"))

from app.db import SessionLocal
from worker.jobs import job_realtime_pipeline
from worker.jobs_refactored import job_realtime_pipeline_refactored
from app.services.data_sources import fetch_latest_1m
from app.services.candle_utils import load_candles_1m_df
from app.services.resample import resample_ohlcv
from app.services.indicators import compute_macd
from utils.market_time import is_market_open
from app.services.debug import debug_helper
from worker.base_worker import BaseRQWorker

class USMacdWorker(BaseRQWorker):
    """OOP wrapper for US MACD realtime processing worker."""

    def get_listen_queues(self) -> list[str]:
        return ['us']

    @staticmethod
    def job_realtime_pipeline_with_macd(symbol_id, symbol, exchange, timeframe_minutes=1):
        """Enhanced realtime pipeline that includes MACD Multi-TF analysis for US symbols"""
        try:
            debug_helper.log_step(f"Starting enhanced realtime pipeline for {symbol} ({exchange})")

            # Check if market is open
            market_open, time_to_close, time_to_open = is_market_open(exchange)
            if not market_open:
                debug_helper.log_step(f"Market closed for {symbol} ({exchange}) - skipping", {
                    'time_to_open': str(time_to_open) if time_to_open else None
                })
                return "market-closed"

            # Check if this symbol is in any active MACD Multi-TF workflow
            macd_config = _get_macd_config_for_symbol(symbol)

            if macd_config:
                debug_helper.log_step(f"Found MACD config for {symbol}, fetching latest data and using regular pipeline")

                # Fetch latest data
                count = fetch_latest_1m(symbol_id, symbol, exchange)
                debug_helper.log_step(f"Fetched {count} new 1m candles for {symbol}")

                # Temporarily use regular realtime pipeline for signal evaluation
                return job_realtime_pipeline_refactored(symbol_id, symbol, exchange, strategy_id=1, force_run=True)
            else:
                # Fall back to regular realtime pipeline
                debug_helper.log_step(f"No MACD config for {symbol}, running regular pipeline")
                return job_realtime_pipeline_refactored(symbol_id, symbol, exchange, strategy_id=1, force_run=True)

        except Exception as e:
            debug_helper.log_step(f"Error in enhanced realtime pipeline for {symbol}", error=e)
            return "error"

# Backward-compatible alias for existing enqueues/imports
job_realtime_pipeline_with_macd = USMacdWorker.job_realtime_pipeline_with_macd

def _get_macd_config_for_symbol(symbol):
    """
    Get MACD configuration for a symbol from active workflows
    """
    try:
        with SessionLocal() as s:
            # Get active workflows with MACD Multi-TF nodes
            result = s.execute(text("""
                SELECT nodes, properties
                FROM workflows 
                WHERE status = 'active'
                AND JSON_SEARCH(nodes, 'one', 'macd-multi') IS NOT NULL
            """)).fetchall()
            
            for nodes_json, properties_json in result:
                nodes = json.loads(nodes_json)
                properties = json.loads(properties_json)
                
                # Find MACD Multi-TF nodes
                macd_multi_nodes = [node for node in nodes if node.get('type') == 'macd-multi']
                
                for node in macd_multi_nodes:
                    node_id = node['id']
                    node_config = properties.get(node_id, {})
                    
                    # Check if this symbol is in the configuration
                    symbol_thresholds = node_config.get('symbolThresholds', [])
                    for symbol_config in symbol_thresholds:
                        if isinstance(symbol_config, dict) and symbol_config.get('symbol', '').upper() == symbol.upper():
                            # Merge node config with symbol-specific config
                            config = dict(node_config)
                            config.update(symbol_config)
                            return config
            
            return None
            
    except Exception as e:
        debug_helper.log_step(f"Error getting MACD config for {symbol}", error=e)
        return None

if __name__ == '__main__':
    # Preserve original CLI behavior
    USMacdWorker().run(with_scheduler=True)
