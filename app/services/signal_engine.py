"""
Signal Engine Module
Contains functions for signal generation and validation
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from app.services.strategy_config import get_strategy_for_symbol
from app.services.symbol_thresholds import get_symbol_thresholds, get_market_thresholds, get_symbol_market_type

def match_zone(value: float, rules: List[Dict], indicator_type: str) -> str:
    """
    Match a value to a zone based on rules (Legacy function - kept for compatibility)
    
    Args:
        value: The value to match
        rules: List of threshold rules
        indicator_type: Type of indicator (fmacd, smacd, bars)
    
    Returns:
        Zone name (e.g., 'bull', 'bear', 'neutral')
    """
    if not rules:
        return 'neutral'
    
    # Find rules for this indicator type
    indicator_rules = [rule for rule in rules if rule.get('indicator') == indicator_type]
    
    if not indicator_rules:
        return 'neutral'
    
    # Sort rules by threshold value
    indicator_rules.sort(key=lambda x: x.get('threshold', 0))
    
    # Match value to zone
    for rule in indicator_rules:
        threshold = rule.get('threshold', 0)
        zone = rule.get('zone', 'neutral')
        
        if indicator_type == 'fmacd' or indicator_type == 'smacd':
            if value >= threshold:
                return zone
        elif indicator_type == 'bars':
            if abs(value) >= threshold:
                return zone
    
    return 'neutral'

def match_zone_with_thresholds(value: float, symbol_id: int, timeframe: str, indicator_type: str) -> str:
    """
    Match a value to a zone using symbol-specific thresholds
    
    Args:
        value: The value to match
        symbol_id: ID of the symbol
        timeframe: Timeframe (1m, 2m, 5m, 15m, 30m, 1h, 4h, 1D)
        indicator_type: Type of indicator (fmacd, smacd, bars)
    
    Returns:
        Zone name (e.g., 'bull', 'bear', 'neutral')
    """
    try:
        # Lấy thresholds cho symbol cụ thể
        thresholds = get_symbol_thresholds(symbol_id, timeframe)
        
        if not thresholds:
            # Fallback to market defaults
            market_type = get_symbol_market_type(symbol_id)
            thresholds = get_market_thresholds(market_type, timeframe)
        
        if not thresholds:
            return 'neutral'
        
        # Find rules for this indicator type
        indicator_rules = [rule for rule in thresholds if rule.get('indicator') == indicator_type]
        
        if not indicator_rules:
            return 'neutral'
        
        # Sort rules by threshold value (descending for bullish zones, ascending for bearish)
        if indicator_type in ['fmacd', 'smacd']:
            # For MACD indicators, sort by min_value descending
            indicator_rules.sort(key=lambda x: x.get('min_value', 0), reverse=True)
        else:
            # For bars, sort by min_value ascending
            indicator_rules.sort(key=lambda x: x.get('min_value', 0))
        
        # Match value to zone
        for rule in indicator_rules:
            min_value = rule.get('min_value', 0)
            max_value = rule.get('max_value')
            comparison = rule.get('comparison', '>=')
            zone = rule.get('zone', 'neutral')
            
            if indicator_type in ['fmacd', 'smacd']:
                # MACD indicators
                if comparison == '>=' and value >= min_value:
                    return zone
                elif comparison == '>' and value > min_value:
                    return zone
                elif comparison == '<' and value < min_value:
                    return zone
                elif comparison == '<=' and value <= min_value:
                    return zone
                elif comparison == 'between' and max_value and min_value <= value <= max_value:
                    return zone
            elif indicator_type == 'bars':
                # Bars indicator (use absolute value)
                abs_value = abs(value)
                if comparison == '>=' and abs_value >= min_value:
                    return zone
                elif comparison == '>' and abs_value > min_value:
                    return zone
                elif comparison == '<' and abs_value < min_value:
                    return zone
                elif comparison == '<=' and abs_value <= min_value:
                    return zone
                elif comparison == 'between' and max_value and min_value <= abs_value <= max_value:
                    return zone
        
        return 'neutral'
        
    except Exception as e:
        print(f"Error in match_zone_with_thresholds: {e}")
        return 'neutral'

def make_signal(f_zone: str, s_zone: str, bars_zone: str, strategy_config=None) -> Optional[str]:
    """
    Generate signal based on zones
    
    Args:
        f_zone: Fast MACD zone
        s_zone: Signal MACD zone  
        bars_zone: Bars zone
        strategy_config: Strategy configuration
    
    Returns:
        Signal type ('BUY', 'SELL', or None)
    """
    if not all([f_zone, s_zone, bars_zone]):
        return None
    
    # Basic signal logic
    if f_zone in ['bull', 'strong_bull', 'greed', 'igr'] and s_zone in ['bull', 'strong_bull', 'greed', 'igr'] and bars_zone in ['bull', 'strong_bull', 'greed', 'igr']:
        return 'BUY'
    elif f_zone in ['bear', 'strong_bear', 'fear', 'panic'] and s_zone in ['bear', 'strong_bear', 'fear', 'panic'] and bars_zone in ['bear', 'strong_bear', 'fear', 'panic']:
        return 'SELL'
    
    # Strategy-specific logic
    if strategy_config:
        # Check if strategy requires all zones to be bullish for BUY signal
        if hasattr(strategy_config, 'require_all_bullish') and strategy_config.require_all_bullish:
            if not all(z in ['bull', 'strong_bull'] for z in [f_zone, s_zone, bars_zone]):
                return None
        # Check if strategy requires all zones to be bearish for SELL signal  
        if hasattr(strategy_config, 'require_all_bearish') and strategy_config.require_all_bearish:
            if not all(z in ['bear', 'strong_bear'] for z in [f_zone, s_zone, bars_zone]):
                return None
    
    return None

def validate_cross_timeframe_synchronization(signals_by_tf: Dict[str, str], strategy_config) -> bool:
    """
    Validate cross-timeframe synchronization
    
    Args:
        signals_by_tf: Dictionary of signals by timeframe
        strategy_config: Strategy configuration
    
    Returns:
        True if synchronized, False otherwise
    """
    if not strategy_config or not strategy_config.require_synchronization:
        return True
    
    if not signals_by_tf:
        return False
    
    # Get high timeframes
    high_tfs = ['1D4hr', '1D1hr', '1D30Min']
    high_tf_signals = [signals_by_tf.get(tf) for tf in high_tfs if tf in signals_by_tf]
    
    if not high_tf_signals:
        return True
    
    # Check if all high timeframe signals are in same direction
    buy_signals = sum(1 for sig in high_tf_signals if sig == 'BUY')
    sell_signals = sum(1 for sig in high_tf_signals if sig == 'SELL')
    
    # Require at least 2/3 of high timeframes to agree
    total_high_tfs = len(high_tf_signals)
    if total_high_tfs < 2:
        return True
    
    return (buy_signals >= total_high_tfs * 0.6) or (sell_signals >= total_high_tfs * 0.6)

def aggregate_signals_with_weights(sig_map: Dict[str, str], tf_weights: Dict[str, float]) -> tuple:
    """
    Aggregate signals with Weighted Scoring System - Linh hoạt hơn consensus cũ
    
    Args:
        sig_map: Dictionary of signals by timeframe
        tf_weights: Dictionary of weights by timeframe
    
    Returns:
        Tuple of (final_signal, score, buy_votes, sell_votes)
    """
    # Use Weighted Scoring with threshold 0.2 for more responsive signals
    final_signal, score_ratio, details = weighted_scoring_aggregation(sig_map, tf_weights, threshold=0.2)
    
    # Convert back to old format for compatibility
    score = details['total_score']
    votes_buy = details['signal_counts']['BUY']
    votes_sell = details['signal_counts']['SELL']
    
    return final_signal, score, votes_buy, votes_sell

def weighted_scoring_aggregation(sig_map: Dict[str, str], tf_weights: Dict[str, float], threshold: float = 0.3) -> tuple:
    """
    Weighted Scoring System - Linh hoạt hơn consensus hiện tại
    
    Args:
        sig_map: Dictionary of signals by timeframe
        tf_weights: Dictionary of weights by timeframe
        threshold: Minimum ratio to generate signal (default 0.3 = 30%)
    
    Returns:
        Tuple of (final_signal, score_ratio, details)
    """
    total_score = 0
    total_weight = 0
    buy_score = 0
    sell_score = 0
    signal_counts = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
    
    for tf_name, signal in sig_map.items():
        weight = tf_weights.get(tf_name, 1)
        total_weight += weight
        
        if signal == 'BUY':
            buy_score += weight
            total_score += weight
            signal_counts['BUY'] += 1
        elif signal == 'SELL':
            sell_score += weight
            total_score -= weight
            signal_counts['SELL'] += 1
        else:
            signal_counts['HOLD'] += 1
    
    if total_weight == 0:
        return 'HOLD', 0.0, {'error': 'No timeframes available'}
    
    score_ratio = total_score / total_weight
    
    # Determine final signal
    if score_ratio >= threshold:
        final_signal = 'BUY'
    elif score_ratio <= -threshold:
        final_signal = 'SELL'
    else:
        final_signal = 'HOLD'
    
    details = {
        'total_score': total_score,
        'total_weight': total_weight,
        'score_ratio': score_ratio,
        'buy_score': buy_score,
        'sell_score': sell_score,
        'signal_counts': signal_counts,
        'threshold': threshold
    }
    
    return final_signal, score_ratio, details
