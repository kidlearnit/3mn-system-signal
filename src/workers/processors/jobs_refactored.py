"""
Refactored jobs module using new design patterns.
This replaces the hardcoded logic in jobs.py with Strategy, Repository, and Pipeline patterns.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from worker.repositories.strategy_config_repository import StrategyConfigRepository
# Import repositories - will be implemented later
# from worker.repositories.market_data_repository import MarketDataRepository
# from worker.repositories.signal_repository import SignalRepository
from worker.strategies.macd_strategy import MACDStrategy
from worker.strategies.base_strategy import MarketData, Signal
from worker.pipeline.base_pipeline import ProcessingPipeline, PipelineContext
from worker.pipeline.data_validation_step import DataValidationStep
from worker.pipeline.indicator_calculation_step import IndicatorCalculationStep
from worker.pipeline.signal_evaluation_step import SignalEvaluationStep
from worker.pipeline.data_fetch_step import DataFetchStep
from worker.integration import notify_signal
from app.services.debug import debug_helper
from app.db import SessionLocal, init_db

# Initialize DB session if not already done
init_db(os.getenv("DATABASE_URL"))

logger = logging.getLogger(__name__)

class RefactoredRealtimePipeline:
    """
    Refactored realtime pipeline using new design patterns.
    Replaces job_realtime_pipeline2 with clean, configurable architecture.
    """
    
    def __init__(self):
        # Initialize repositories
        repo_config = {
            'cache_enabled': True,
            'cache_ttl': 60,
            'rt_fetch_minutes': int(os.getenv('RT_FETCH_MINUTES', '180')),
            'rt_lookback_minutes': int(os.getenv('RT_LOOKBACK_MINUTES', '1440'))
        }
        
        self.strategy_config_repo = StrategyConfigRepository(repo_config)
        # TODO: Implement market_data_repo and signal_repo
        # self.market_data_repo = MarketDataRepository(repo_config)
        # self.signal_repo = SignalRepository(repo_config)
        
        # Initialize strategies
        self.strategies = {}
        
        logger.info("RefactoredRealtimePipeline initialized")

    def process_symbol(self, symbol_id: int, ticker: str, exchange: str, strategy_id: int = 1, force_run: bool = False) -> str:
        """
        Process a single symbol through the refactored pipeline.
        """
        try:
            debug_helper.log_step(f"Starting refactored pipeline for {ticker}", {
                'symbol_id': symbol_id,
                'ticker': ticker,
                'exchange': exchange,
                'strategy_id': strategy_id
            })
            
            # Get strategy configuration
            macd_config = self.strategy_config_repo.get_macd_config(ticker)
            debug_helper.log_step(f"MACD config for {ticker}", macd_config)
            
            # Create MACD strategy with configuration
            macd_strategy = MACDStrategy(
                name=f"MACD_{ticker}",
                fast_period=macd_config.get('fastPeriod', 7),
                slow_period=macd_config.get('slowPeriod', 72),
                signal_period=macd_config.get('signalPeriod', 144)
            )
            self.strategies[ticker] = macd_strategy
            
            # Fetch market data using existing infrastructure
            from app.services.data_sources import get_realtime_df_1m
            df_1m = get_realtime_df_1m(ticker, exchange, minutes=int(os.getenv('RT_FETCH_MINUTES', '180')))
            if df_1m is None or df_1m.empty:
                debug_helper.log_step(f"No data for {ticker}", "Returning no-data")
                return "no-data"
            
            debug_helper.log_step(f"Fetched data for {ticker}", f"Rows: {len(df_1m)}")
            
            # Create market data object
            market_data = MarketData(
                symbol=ticker,
                exchange=exchange,
                timeframe="1m",
                candles=df_1m,
                timestamp=datetime.now()
            )
            
            # Process through pipeline
            pipeline = self._create_processing_pipeline(ticker, macd_config)
            context = PipelineContext(market_data=market_data)
            
            # Execute pipeline
            final_context = pipeline.execute(context)
            
            if final_context.errors:
                logger.error(f"Pipeline errors for {ticker}: {final_context.errors}")
                return "pipeline-error"
            
            # Process signals
            if final_context.signals:
                signal = final_context.signals[0]  # Take first signal
                result = self._process_signal(signal, symbol_id, strategy_id, ticker, exchange)
                debug_helper.log_step(f"Processed signal for {ticker}", result)
                return result
            else:
                debug_helper.log_step(f"No signals generated for {ticker}", "Returning no-signal")
                return "no-signal"
                
        except Exception as e:
            logger.error(f"Error in refactored pipeline for {ticker}: {e}")
            debug_helper.log_step(f"Pipeline error for {ticker}", error=e)
            return "error"

    def _create_processing_pipeline(self, ticker: str, macd_config: Dict[str, Any]) -> ProcessingPipeline:
        """
        Create a processing pipeline with appropriate steps.
        """
        pipeline = ProcessingPipeline(f"MACD_Pipeline_{ticker}")
        
        # Add data validation step
        min_candles = max(macd_config.get('slowPeriod', 72), macd_config.get('signalPeriod', 144)) * 2
        validation_step = DataValidationStep(min_candles=min_candles)
        pipeline.add_step(validation_step)
        
        # Add indicator calculation step
        macd_strategy = self.strategies.get(ticker)
        if macd_strategy:
            indicator_step = IndicatorCalculationStep(strategies=[macd_strategy])
            pipeline.add_step(indicator_step)
        
        # Add signal evaluation step
        if macd_strategy:
            signal_step = SignalEvaluationStep(strategies=[macd_strategy])
            pipeline.add_step(signal_step)
        
        return pipeline

    def _process_signal(self, signal: Signal, symbol_id: int, strategy_id: int, ticker: str, exchange: str) -> str:
        """
        Process a generated signal: save to DB and send notifications.
        """
        try:
            # Save signal to database using existing infrastructure
            from worker.jobs import save_signal_to_db
            save_signal_to_db(symbol_id, signal.signal_type, signal.strength, strategy_id, {
                k: {'signal': v} for k, v in signal.details.get('per_tf_signals', {}).items()
            })
            debug_helper.log_step(f"Saved signal for {ticker}", signal.signal_type)
            
            # Send notification via Observer system
            notify_result = notify_signal(
                symbol=ticker,
                timeframe=signal.timeframe,
                signal_type=signal.signal_type,
                confidence=signal.confidence,
                strength=signal.strength,
                strategy_name=signal.strategy_name,
                details=signal.details
            )
            
            if notify_result:
                debug_helper.log_step(f"Notification sent for {ticker}", "Success")
            else:
                debug_helper.log_step(f"Notification failed for {ticker}", "Failed")
            
            return signal.signal_type
            
        except Exception as e:
            logger.error(f"Error processing signal for {ticker}: {e}")
            return "signal-error"

    def process_multiple_timeframes(self, symbol_id: int, ticker: str, exchange: str, strategy_id: int = 1) -> str:
        """
        Process symbol across multiple timeframes using the new architecture.
        This replaces the hardcoded multi-TF logic in the original jobs.py.
        """
        try:
            # Get strategy configuration
            macd_config = self.strategy_config_repo.get_macd_config(ticker)
            tf_list = macd_config.get('tf_list', ['2m', '5m', '15m', '30m', '1h'])
            min_consensus = macd_config.get('min_consensus', 3)
            
            debug_helper.log_step(f"Processing {ticker} across timeframes", {
                'tf_list': tf_list,
                'min_consensus': min_consensus
            })
            
            # Fetch 1m data using existing infrastructure
            from app.services.data_sources import get_realtime_df_1m
            df_1m = get_realtime_df_1m(ticker, exchange, minutes=int(os.getenv('RT_FETCH_MINUTES', '180')))
            if df_1m is None or df_1m.empty:
                return "no-data"
            
            # Process each timeframe
            per_tf_signals = {}
            for tf in tf_list:
                try:
                    # Get TF candles using existing infrastructure
                    from app.services.resample import resample_ohlcv
                    from worker.jobs import load_recent_candles_tf, upsert_candles_tf
                    
                    df_tf = load_recent_candles_tf(symbol_id, tf, max_bars=500)
                    if df_tf.empty:
                        # Resample from 1m if no TF data
                        df_tf = resample_ohlcv(df_1m, tf)
                        if not df_tf.empty:
                            upsert_candles_tf(symbol_id, tf, df_tf)
                    
                    if df_tf.empty:
                        continue
                    
                    # Calculate MACD indicators
                    macd_strategy = MACDStrategy(
                        name=f"MACD_{ticker}_{tf}",
                        fast_period=macd_config.get('fastPeriod', 7),
                        slow_period=macd_config.get('slowPeriod', 72),
                        signal_period=macd_config.get('signalPeriod', 144)
                    )
                    
                    # Create market data for this timeframe
                    market_data = MarketData(
                        symbol=ticker,
                        exchange=exchange,
                        timeframe=tf,
                        candles=df_tf,
                        timestamp=datetime.now()
                    )
                    
                    # Generate signal for this timeframe
                    signal = macd_strategy.generate_signal(market_data)
                    if signal:
                        per_tf_signals[tf] = signal.signal_type
                        debug_helper.log_step(f"Signal for {ticker} {tf}", signal.signal_type)
                    else:
                        per_tf_signals[tf] = None
                        
                except Exception as tf_error:
                    debug_helper.log_step(f"Error processing {tf} for {ticker}", error=tf_error)
                    continue
            
            # Calculate consensus
            votes_buy = sum(1 for v in per_tf_signals.values() if v == 'BUY')
            votes_sell = sum(1 for v in per_tf_signals.values() if v == 'SELL')
            
            final_sig = None
            if votes_buy >= min_consensus:
                final_sig = 'BUY'
            elif votes_sell >= min_consensus:
                final_sig = 'SELL'
            
            debug_helper.log_step(f"Consensus for {ticker}", {
                'signals': per_tf_signals,
                'votes_buy': votes_buy,
                'votes_sell': votes_sell,
                'final': final_sig
            })
            
            if final_sig:
                # Create final signal
                final_signal = Signal(
                    symbol=ticker,
                    exchange=exchange,
                    timeframe="multi_tf",
                    signal_type=final_sig,
                    confidence=float(max(votes_buy, votes_sell) / len(tf_list)),
                    strength=float(abs(votes_buy - votes_sell)),
                    timestamp=datetime.now(),
                    strategy_name='MACD_Multi_TF_Consensus',
                    details={
                        'per_tf_signals': per_tf_signals,
                        'votes_buy': votes_buy,
                        'votes_sell': votes_sell,
                        'exchange': exchange,
                        'macd_config': macd_config
                    }
                )
                
                return self._process_signal(final_signal, symbol_id, strategy_id, ticker, exchange)
            else:
                return "no-consensus"
                
        except Exception as e:
            logger.error(f"Error in multi-TF processing for {ticker}: {e}")
            return "error"


# Global instance for use in jobs
_refactored_pipeline = None

def get_refactored_pipeline() -> RefactoredRealtimePipeline:
    """Get or create the global refactored pipeline instance."""
    global _refactored_pipeline
    if _refactored_pipeline is None:
        _refactored_pipeline = RefactoredRealtimePipeline()
    return _refactored_pipeline


# New job functions that use the refactored pipeline
def job_realtime_pipeline_refactored(symbol_id: int, ticker: str, exchange: str, strategy_id: int = 1, force_run: bool = False) -> str:
    """
    Refactored realtime pipeline job using new design patterns.
    This replaces job_realtime_pipeline2 with clean, configurable architecture.
    """
    pipeline = get_refactored_pipeline()
    return pipeline.process_multiple_timeframes(symbol_id, ticker, exchange, strategy_id)


def job_realtime_pipeline_single_tf(symbol_id: int, ticker: str, exchange: str, strategy_id: int = 1, force_run: bool = False) -> str:
    """
    Single timeframe processing using refactored pipeline.
    """
    pipeline = get_refactored_pipeline()
    return pipeline.process_symbol(symbol_id, ticker, exchange, strategy_id, force_run)
