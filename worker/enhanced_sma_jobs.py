#!/usr/bin/env python3
"""
Enhanced SMA Jobs - Professional Trading Signals
Integrates Enhanced Signal Engine with risk management and portfolio insights
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import app.db as db
from app.services.enhanced_signal_engine import enhanced_signal_engine, EnhancedSignalType
from app.services.portfolio_manager import portfolio_manager
from app.services.debug import debug_helper
from worker.sma_jobs import store_sma_indicators, TF_LIST_SMA
from worker.jobs import load_candles_1m_df, upsert_candles_tf
from app.services.data_sources import fetch_latest_1m
from app.services.resample import resample_ohlcv
from app.services.sma_indicators import sma_indicator_service
from utils.market_time import is_market_open

logger = logging.getLogger(__name__)

def job_enhanced_sma_pipeline(symbol_id: int, ticker: str, exchange: str):
    """
    Enhanced SMA Pipeline Job - Professional trading signals with risk management
    """
    try:
        debug_helper.log_step(f"Starting Enhanced SMA pipeline for {ticker}", {
            'symbol_id': symbol_id,
            'ticker': ticker,
            'exchange': exchange
        })
        
        # 1. Check market status
        market_open, _, _ = is_market_open(exchange)
        if not market_open:
            debug_helper.log_step(f"Market closed for {ticker} ({exchange}) - skipping pipeline")
            return "market-closed"
        
        # 2. Lấy nến 1m mới nhất
        debug_helper.log_step(f"Fetching latest 1m data for {ticker}")
        count = fetch_latest_1m(symbol_id, ticker, exchange)
        debug_helper.log_step(f"Latest 1m data fetch result for {ticker}", f"Count: {count}")

        # 3. Load 1m candles từ DB
        debug_helper.log_step(f"Loading 1m candles from DB for {ticker}")
        df_1m = load_candles_1m_df(symbol_id)
        debug_helper.log_step(f"Loaded 1m candles for {ticker}", f"Rows: {len(df_1m)}")
        
        if df_1m.empty:
            debug_helper.log_step(f"No candles in DB for {ticker}", "Returning no-data")
            return "no-data"
        
        # 4. Process all timeframes and collect enhanced signals
        enhanced_signals = {}
        try:
            for tf in TF_LIST_SMA:
                debug_helper.log_step(f"Processing Enhanced SMA timeframe {tf} for {ticker}")
                
                try:
                    # Resample data
                    df_tf = resample_ohlcv(df_1m, tf)
                    debug_helper.log_step(f"Resampled {tf} for {ticker}", f"Rows: {len(df_tf)}")
                    
                    # Upsert candles
                    upsert_candles_tf(symbol_id, tf, df_tf)
                    debug_helper.log_step(f"Upserted {tf} candles for {ticker}")
                    
                    # Calculate SMA indicators
                    sma_results = sma_indicator_service.calculate_all_smas(df_tf)
                    
                    # Add SMA columns to dataframe
                    df_sma = df_tf.copy()
                    for name, series in sma_results.items():
                        df_sma[name] = series
                    
                    # Store SMA indicators
                    store_sma_indicators(symbol_id, tf, df_sma)
                    debug_helper.log_step(f"Stored SMA indicators for {symbol_id} {tf}")
                    
                    # Generate enhanced signal
                    enhanced_signal = _generate_enhanced_signal_for_timeframe(
                        symbol_id, ticker, exchange, tf, df_sma
                    )
                    
                    if enhanced_signal:
                        enhanced_signals[tf] = enhanced_signal
                        debug_helper.log_step(f"Generated enhanced signal for {ticker} {tf}", {
                            'signal_type': enhanced_signal['signal_type'],
                            'confidence': enhanced_signal['confidence_score'],
                            'risk_score': enhanced_signal['risk_score']
                        })
                    
                except Exception as e:
                    debug_helper.log_step(f"Error processing {tf} for {ticker}", error=e)
                    continue
            
            # 5. Multi-timeframe analysis
            if enhanced_signals:
                multi_tf_analysis = _analyze_multi_timeframe_signals(enhanced_signals)
                debug_helper.log_step(f"Multi-timeframe analysis for {ticker}", multi_tf_analysis)
                
                # 6. Portfolio management integration
                _integrate_with_portfolio_manager(symbol_id, ticker, exchange, enhanced_signals, multi_tf_analysis)
            
            debug_helper.log_step(f"Completed Enhanced SMA pipeline for {ticker}")
            return "success"
            
        except Exception as e:
            debug_helper.log_step(f"Error in Enhanced SMA pipeline for {ticker}", error=e)
            return "error"
            
    except Exception as e:
        debug_helper.log_step(f"Critical error in Enhanced SMA pipeline for {ticker}", error=e)
        return "critical-error"

def _generate_enhanced_signal_for_timeframe(symbol_id: int, ticker: str, exchange: str, 
                                          timeframe: str, df_sma: Any) -> Optional[Dict[str, Any]]:
    """Generate enhanced signal for a specific timeframe"""
    
    try:
        if df_sma.empty or len(df_sma) < 50:
            return None
        
        # Get latest MA structure
        latest_row = df_sma.iloc[0]
        ma_structure = {
            'cp': float(latest_row['close']),
            'm1': float(latest_row.get('sma_18', latest_row['close'])),
            'm2': float(latest_row.get('sma_36', latest_row['close'])),
            'm3': float(latest_row.get('sma_48', latest_row['close'])),
            'ma144': float(latest_row.get('sma_144', latest_row['close']))
        }
        
        # Get volume data
        volume_data = {
            'current': float(latest_row['volume']),
            'average': float(df_sma['volume'].mean()),
            'max': float(df_sma['volume'].max())
        }
        
        # Generate enhanced signal
        enhanced_signal = enhanced_signal_engine.generate_enhanced_signal(
            df_sma, ma_structure, volume_data
        )
        
        # Add metadata
        enhanced_signal['symbol_id'] = symbol_id
        enhanced_signal['ticker'] = ticker
        enhanced_signal['exchange'] = exchange
        enhanced_signal['timeframe'] = timeframe
        enhanced_signal['timestamp'] = datetime.now()
        
        return enhanced_signal
        
    except Exception as e:
        debug_helper.log_step(f"Error generating enhanced signal for {ticker} {timeframe}", error=e)
        return None

def _analyze_multi_timeframe_signals(enhanced_signals: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze signals across multiple timeframes"""
    
    try:
        timeframes = list(enhanced_signals.keys())
        signals = list(enhanced_signals.values())
        
        # Count signal types
        signal_counts = {}
        confidence_scores = []
        risk_scores = []
        
        for signal in signals:
            signal_type = signal['signal_type']
            signal_counts[signal_type] = signal_counts.get(signal_type, 0) + 1
            confidence_scores.append(signal['confidence_score'])
            risk_scores.append(signal['risk_score'])
        
        # Calculate aggregate metrics
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        
        # Determine overall signal
        overall_signal = _determine_overall_signal(signal_counts, avg_confidence, avg_risk)
        
        return {
            'timeframes_analyzed': timeframes,
            'signal_counts': signal_counts,
            'average_confidence': avg_confidence,
            'average_risk': avg_risk,
            'overall_signal': overall_signal,
            'signal_consistency': _calculate_signal_consistency(signal_counts),
            'risk_assessment': _assess_overall_risk(risk_scores)
        }
        
    except Exception as e:
        debug_helper.log_step(f"Error in multi-timeframe analysis", error=e)
        return {}

def _determine_overall_signal(signal_counts: Dict[str, int], 
                            avg_confidence: float, avg_risk: float) -> str:
    """Determine overall signal from multi-timeframe analysis"""
    
    # Count bullish vs bearish signals
    bullish_signals = sum(signal_counts.get(signal, 0) for signal in 
                         ['strong_buy', 'buy', 'weak_buy'])
    bearish_signals = sum(signal_counts.get(signal, 0) for signal in 
                         ['strong_sell', 'sell', 'weak_sell'])
    neutral_signals = signal_counts.get('hold', 0)
    
    total_signals = bullish_signals + bearish_signals + neutral_signals
    
    if total_signals == 0:
        return 'no_signals'
    
    # Determine based on majority and confidence
    if bullish_signals > bearish_signals and bullish_signals > neutral_signals:
        if avg_confidence >= 0.7 and avg_risk <= 0.4:
            return 'strong_bullish'
        elif avg_confidence >= 0.5 and avg_risk <= 0.6:
            return 'bullish'
        else:
            return 'weak_bullish'
    elif bearish_signals > bullish_signals and bearish_signals > neutral_signals:
        if avg_confidence >= 0.7 and avg_risk <= 0.4:
            return 'strong_bearish'
        elif avg_confidence >= 0.5 and avg_risk <= 0.6:
            return 'bearish'
        else:
            return 'weak_bearish'
    else:
        return 'neutral'

def _calculate_signal_consistency(signal_counts: Dict[str, int]) -> float:
    """Calculate signal consistency across timeframes"""
    
    total_signals = sum(signal_counts.values())
    if total_signals == 0:
        return 0.0
    
    # Find the most common signal
    max_count = max(signal_counts.values())
    consistency = max_count / total_signals
    
    return consistency

def _assess_overall_risk(risk_scores: list) -> str:
    """Assess overall risk level"""
    
    if not risk_scores:
        return 'unknown'
    
    avg_risk = sum(risk_scores) / len(risk_scores)
    
    if avg_risk <= 0.3:
        return 'low'
    elif avg_risk <= 0.6:
        return 'medium'
    else:
        return 'high'

def _integrate_with_portfolio_manager(symbol_id: int, ticker: str, exchange: str,
                                    enhanced_signals: Dict[str, Dict[str, Any]],
                                    multi_tf_analysis: Dict[str, Any]):
    """Integrate enhanced signals with portfolio management"""
    
    try:
        # Get the strongest signal (highest confidence)
        strongest_signal = None
        highest_confidence = 0
        
        for tf, signal in enhanced_signals.items():
            if signal['confidence_score'] > highest_confidence:
                highest_confidence = signal['confidence_score']
                strongest_signal = signal
        
        if not strongest_signal:
            return
        
        # Check if we should open a position
        signal_type = strongest_signal['signal_type']
        confidence = strongest_signal['confidence_score']
        risk_metrics = strongest_signal['risk_metrics']
        
        # Only consider strong signals for position opening
        if signal_type in ['strong_buy', 'strong_sell'] and confidence >= 0.7:
            
            # Determine position side
            side = 'long' if 'buy' in signal_type else 'short'
            
            # Calculate position size
            position_size = portfolio_manager.calculate_position_size(
                ticker, 
                risk_metrics.stop_loss,  # Using current price as entry
                risk_metrics.stop_loss,
                confidence
            )
            
            if position_size > 0:
                # Check if we can open position
                current_price = strongest_signal['ma_structure']['cp']
                
                success = portfolio_manager.open_position(
                    symbol=ticker,
                    exchange=exchange,
                    side=side,
                    size=position_size,
                    entry_price=current_price,
                    stop_loss=risk_metrics.stop_loss,
                    take_profit=risk_metrics.take_profit,
                    signal_confidence=confidence
                )
                
                if success:
                    debug_helper.log_step(f"Opened {side} position for {ticker}", {
                        'size': position_size,
                        'entry_price': current_price,
                        'stop_loss': risk_metrics.stop_loss,
                        'take_profit': risk_metrics.take_profit
                    })
                else:
                    debug_helper.log_step(f"Failed to open position for {ticker} - portfolio constraints")
        
        # Update existing positions
        portfolio_manager.update_positions({ticker: strongest_signal['ma_structure']['cp']})
        
        # Check stop losses and take profits
        closed_stops = portfolio_manager.check_stop_losses({ticker: strongest_signal['ma_structure']['cp']})
        closed_takes = portfolio_manager.check_take_profits({ticker: strongest_signal['ma_structure']['cp']})
        
        if closed_stops:
            debug_helper.log_step(f"Closed positions due to stop loss: {closed_stops}")
        if closed_takes:
            debug_helper.log_step(f"Closed positions due to take profit: {closed_takes}")
        
    except Exception as e:
        debug_helper.log_step(f"Error integrating with portfolio manager for {ticker}", error=e)

def get_portfolio_summary() -> Dict[str, Any]:
    """Get portfolio summary for monitoring"""
    
    try:
        metrics = portfolio_manager.get_portfolio_metrics()
        position_summary = portfolio_manager.get_position_summary()
        
        return {
            'metrics': {
                'total_value': metrics.total_value,
                'total_pnl': metrics.total_pnl,
                'total_pnl_pct': metrics.total_pnl_pct,
                'daily_pnl': metrics.daily_pnl,
                'daily_pnl_pct': metrics.daily_pnl_pct,
                'max_drawdown': metrics.max_drawdown,
                'sharpe_ratio': metrics.sharpe_ratio,
                'win_rate': metrics.win_rate,
                'profit_factor': metrics.profit_factor,
                'total_trades': metrics.total_trades,
                'open_positions': metrics.open_positions,
                'total_risk': metrics.total_risk
            },
            'positions': position_summary
        }
        
    except Exception as e:
        debug_helper.log_step(f"Error getting portfolio summary", error=e)
        return {}

# Global functions for backward compatibility
def job_sma_pipeline(symbol_id: int, ticker: str, exchange: str):
    """Backward compatibility wrapper"""
    return job_enhanced_sma_pipeline(symbol_id, ticker, exchange)
