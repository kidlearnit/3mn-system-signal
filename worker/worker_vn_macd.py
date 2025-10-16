import os
import json
import logging
from sqlalchemy import text
from datetime import datetime
import pytz

# Import DB và init
from app.db import init_db
init_db(os.getenv("DATABASE_URL"))

from app.db import SessionLocal
from worker.jobs import job_realtime_pipeline
from app.services.data_sources import fetch_latest_1m
from app.services.candle_utils import load_candles_1m_df
from app.services.resample import resample_ohlcv
from app.services.indicators import compute_macd
from utils.market_time import is_market_open
from app.services.debug import debug_helper
from worker.base_worker import BaseRQWorker
from app.services.vn_signal_engine import vn_signal_engine
from app.services.sma_telegram_service import SMATelegramService

logger = logging.getLogger(__name__)

# Initialize Telegram service
telegram_service = SMATelegramService()

# Track last sent signals to avoid spam
last_sent_signals = {}

VN30_TIMEFRAMES = ['1m', '2m', '5m']

class VNMacdWorker(BaseRQWorker):
    """OOP wrapper for VN MACD realtime processing worker."""

    def get_listen_queues(self) -> list[str]:
        return ['vn']

    @staticmethod
    def job_realtime_pipeline_with_macd(symbol_id, symbol, exchange, timeframe_minutes=1):
        """Enhanced realtime pipeline that includes VN signal engine for VN30"""
        try:
            debug_helper.log_step(f"Starting enhanced realtime pipeline for {symbol} ({exchange})")

            # Check if market is open
            market_open, time_to_close, time_to_open = is_market_open(exchange)
            if not market_open:
                debug_helper.log_step(f"Market closed for {symbol} ({exchange}) - skipping", {
                    'time_to_open': str(time_to_open) if time_to_open else None
                })
                return "market-closed"

            # Special handling for VN30 index
            if symbol.upper() == 'VN30':
                return _process_vn30_hybrid_signal(symbol_id, symbol, exchange)
            
            # For other VN symbols, use regular pipeline
            debug_helper.log_step(f"Using regular pipeline for {symbol}")
            return job_realtime_pipeline(symbol_id, symbol, exchange, strategy_id=1, force_run=True)

        except Exception as e:
            debug_helper.log_step(f"Error in enhanced realtime pipeline for {symbol}", error=e)
            return "error"

# Backward-compatible alias for existing enqueues/imports
job_realtime_pipeline_with_macd = VNMacdWorker.job_realtime_pipeline_with_macd

def _process_vn30_hybrid_signal(symbol_id, symbol, exchange):
    """Process VN30 using hybrid signal engine with 3 timeframes"""
    try:
        logger.info(f"🔄 Processing VN30 hybrid signal (1m, 2m, 5m)")
        
        results = []
        for timeframe in VN30_TIMEFRAMES:
            try:
                result = vn_signal_engine.evaluate(symbol_id, symbol, exchange, timeframe)
                if result and result.get('signal') != 'NEUTRAL':
                    results.append(result)
                    logger.info(f"✅ {timeframe}: {result.get('signal')} (confidence: {result.get('confidence', 0):.2f})")
                else:
                    logger.info(f"➡️ {timeframe}: NEUTRAL or error")
            except Exception as e:
                logger.error(f"Error processing {timeframe}: {e}")
        
        # Aggregate results
        if results:
            signals = [r.get('signal') for r in results]
            confidences = [r.get('confidence', 0) for r in results]
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Majority vote for direction
            directions = [r.get('direction') for r in results]
            direction_counts = {}
            for d in directions:
                direction_counts[d] = direction_counts.get(d, 0) + 1
            overall_direction = max(direction_counts, key=direction_counts.get) if direction_counts else 'NEUTRAL'
            
            # Determine overall signal
            if avg_confidence > 0.7:
                overall_signal = f'STRONG_{overall_direction}' if overall_direction != 'NEUTRAL' else 'NEUTRAL'
            elif avg_confidence > 0.5:
                overall_signal = overall_direction if overall_direction != 'NEUTRAL' else 'NEUTRAL'
            else:
                overall_signal = 'NEUTRAL'
            
            logger.info(f"📊 VN30 Overall: {overall_signal} (confidence: {avg_confidence:.2f})")
            
            # Send Telegram if strong signal
            if overall_signal != 'NEUTRAL' and overall_signal != 'NEUTRAL':
                signal_key = f"vn30_{overall_signal}_{int(datetime.now().timestamp() / 60)}"  # Group by minute
                if signal_key not in last_sent_signals:
                    try:
                        message = _create_vn30_telegram_message(symbol, exchange, results, overall_signal, avg_confidence)
                        telegram_service._send_telegram_message(message)
                        last_sent_signals[signal_key] = True
                        logger.info(f"✅ Telegram signal sent: {overall_signal}")
                    except Exception as e:
                        logger.error(f"Error sending Telegram: {e}")
            
            return "vn30-processed"
        else:
            logger.info("⚠️ No significant signals generated")
            return "no-signals"
            
    except Exception as e:
        logger.error(f"Error processing VN30 hybrid signal: {e}")
        return "error"

def _create_vn30_telegram_message(symbol, exchange, results, overall_signal, avg_confidence):
    """Create Telegram message for VN30 signal"""
    signal_icons = {
        'STRONG_BUY': '🚀', 'BUY': '🟢', 'WEAK_BUY': '📈',
        'NEUTRAL': '⚪',
        'WEAK_SELL': '📉', 'SELL': '🔴', 'STRONG_SELL': '💥'
    }
    
    header = f"{signal_icons.get(overall_signal, '❓')} *VN30 Hybrid Signal - {overall_signal}*\n"
    header += f"📊 Confidence: {avg_confidence:.2f}\n"
    header += f"⏰ {datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%H:%M:%S %d/%m/%Y VN')}\n"
    header += "─" * 40 + "\n"
    
    details = "*Timeframe Signals:*\n"
    for r in results:
        tf = r.get('timeframe', 'N/A')
        sig = r.get('signal', 'N/A')
        conf = r.get('confidence', 0)
        details += f"  {tf}: {sig} (conf: {conf:.2f})\n"
    
    footer = "\n" + "─" * 40 + "\n"
    footer += "⚠️ *Disclaimer:* Chỉ là tín hiệu tham khảo, không phải lời khuyên đầu tư"
    
    return header + details + footer

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
    VNMacdWorker().run(with_scheduler=True)
