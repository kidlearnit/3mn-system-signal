import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from app.services.strategy_config import get_strategy_for_symbol

def ema(series, n):
    alpha = 2/(n+1)
    return series.ewm(alpha=alpha, adjust=False).mean()

def compute_macd(df):
    """Tính MACD cho DataFrame. Chấp nhận 'Close' hoặc 'close'."""
    if 'Close' in df.columns:
        df_close = df['Close']
    elif 'close' in df.columns:
        df_close = df['close']
    else:
        raise ValueError("DataFrame must have 'Close' or 'close' column")
    ema12 = ema(df_close, 7)
    ema26 = ema(df_close, 72)
    macd = ema12 - ema26
    signal = ema(macd, 144)
    hist = macd - signal
    
    out = pd.DataFrame({
        'macd': macd, 
        'signal': signal, 
        'hist': hist
    }, index=df.index)
    return out.dropna()

def compute_macd_772144(series, fast=7, slow=72, signal=144):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - signal_line
    return pd.DataFrame({'macd': macd, 'signal': signal_line, 'hist': hist}).dropna()


def compute_3m2_structure(df: pd.DataFrame, period: int = 3) -> pd.DataFrame:
    """
    Compute 3M2 Structure for trend uniformity
    3M2 = 3 Moving Average with 2-period difference
    """
    if len(df) < period + 4:
        return pd.DataFrame()
    
    close = df['close']
    
    # Calculate 3 moving averages
    ma1 = close.rolling(window=period).mean()
    ma2 = close.rolling(window=period + 2).mean()
    ma3 = close.rolling(window=period + 4).mean()
    
    # Structure strength calculation
    # Uniform when all MAs are trending in same direction
    ma1_diff = ma1.diff()
    ma2_diff = ma2.diff()
    ma3_diff = ma3.diff()
    
    # Count how many MAs are trending in same direction
    bullish_count = ((ma1_diff > 0) & (ma2_diff > 0) & (ma3_diff > 0)).astype(int)
    bearish_count = ((ma1_diff < 0) & (ma2_diff < 0) & (ma3_diff < 0)).astype(int)
    
    # Structure strength: 1 = strong uniform, 0 = weak/separate
    structure_strength = bullish_count - bearish_count
    
    # Structure uniformity (0-1 scale)
    uniformity = np.abs(structure_strength)
    
    return pd.DataFrame({
        'ma1': ma1,
        'ma2': ma2,
        'ma3': ma3,
        'structure_strength': structure_strength,
        'uniformity': uniformity
    })

def compute_bars_mt(df: pd.DataFrame, zone_thresholds: Dict[str, float]) -> pd.DataFrame:
    """
    Compute Bars Momentum/Strength (MT)
    Based on price action and volume
    """
    if len(df) < 10:
        return pd.DataFrame()
    
    high = df['high']
    low = df['low']
    close = df['close']
    volume = df['volume']
    
    # Price momentum
    price_change = close.pct_change()
    price_momentum = price_change.rolling(window=5).mean()
    
    # Volume momentum
    volume_ma = volume.rolling(window=10).mean()
    volume_ratio = volume / volume_ma
    
    # Volatility (Bars strength)
    volatility = (high - low) / close
    avg_volatility = volatility.rolling(window=10).mean()
    volatility_ratio = volatility / avg_volatility
    
    # Combined momentum score
    momentum_score = (price_momentum * 0.4 + 
                     volume_ratio * 0.3 + 
                     volatility_ratio * 0.3)
    
    # Convert to zones based on thresholds
    bars_mt_zone = pd.Series(0, index=df.index)
    for zone_name, threshold in zone_thresholds.items():
        if zone_name == 'weak_bear':
            bars_mt_zone[momentum_score < -threshold] = -2
        elif zone_name == 'bear':
            bars_mt_zone[(momentum_score >= -threshold) & (momentum_score < -threshold/2)] = -1
        elif zone_name == 'neutral':
            bars_mt_zone[(momentum_score >= -threshold/2) & (momentum_score <= threshold/2)] = 0
        elif zone_name == 'bull':
            bars_mt_zone[(momentum_score > threshold/2) & (momentum_score <= threshold)] = 1
        elif zone_name == 'weak_bull':
            bars_mt_zone[momentum_score > threshold] = 2
    
    return pd.DataFrame({
        'momentum_score': momentum_score,
        'bars_mt_zone': bars_mt_zone,
        'price_momentum': price_momentum,
        'volume_ratio': volume_ratio,
        'volatility_ratio': volatility_ratio
    })

def compute_momentum_formula(bar_mt_zone: pd.Series, smacd_zone: pd.Series) -> pd.Series:
    """
    Compute MT using formula: MT = Bar MT (Zone) - SMACD (Zone)
    """
    return bar_mt_zone - smacd_zone

def compute_rsi(series, period=14):
    """Calculate RSI (Relative Strength Index)"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_sma(series, period):
    """Calculate Simple Moving Average"""
    return series.rolling(window=period).mean()

def compute_bollinger_bands(df, period=20, std_dev=2):
    """Calculate Bollinger Bands. Chấp nhận 'Close' hoặc 'close'."""
    if 'Close' in df.columns:
        close = df['Close']
    elif 'close' in df.columns:
        close = df['close']
    else:
        raise ValueError("DataFrame must have 'Close' or 'close' column")
    middle = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return pd.DataFrame({
        'upper': upper,
        'middle': middle,
        'lower': lower
    }, index=df.index).dropna()

def compute_advanced_indicators(df: pd.DataFrame, symbol_id: int, strategy_config=None) -> pd.DataFrame:
    """
    Compute advanced indicators based on strategy configuration
    """
    if strategy_config is None:
        strategy_config = get_strategy_for_symbol(symbol_id)
    
    if strategy_config is None:
        return pd.DataFrame()
    
    result_df = df.copy()
    
    # Always compute basic MACD
    macd_df = compute_macd_772144(df['close'])
    result_df = pd.concat([result_df, macd_df], axis=1)
    
    # Compute additional indicators based on strategy
    if strategy_config.use_3m2_structure:
        structure_df = compute_3m2_structure(df)
        result_df = pd.concat([result_df, structure_df], axis=1)
    
    if strategy_config.use_bars_mt:
        # Default zone thresholds - should be configurable
        zone_thresholds = {
            'weak_bear': 0.05,
            'bear': 0.03,
            'neutral': 0.01,
            'bull': 0.03,
            'weak_bull': 0.05
        }
        bars_mt_df = compute_bars_mt(df, zone_thresholds)
        result_df = pd.concat([result_df, bars_mt_df], axis=1)
        
        if strategy_config.use_momentum_formula:
            # Need SMACD zone - this would come from signal_engine
            # For now, use simple MACD signal as proxy
            smacd_zone = pd.Series(0, index=df.index)
            smacd_zone[result_df['signal'] > 0] = 1
            smacd_zone[result_df['signal'] < 0] = -1
            
            mt_formula = compute_momentum_formula(bars_mt_df['bars_mt_zone'], smacd_zone)
            result_df['mt_formula'] = mt_formula
    
    return result_df