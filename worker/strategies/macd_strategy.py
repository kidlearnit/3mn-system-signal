"""
MACD Strategy Implementation

This module implements the MACD (Moving Average Convergence Divergence) 
trading strategy with configurable parameters and threshold-based signal generation.
"""

from typing import Optional, Dict, Any
import pandas as pd
from datetime import datetime

from .base_strategy import SignalStrategy, MarketData, Signal
from app.services.indicators import compute_macd_772144
from app.services.debug import debug_helper


class MACDStrategy(SignalStrategy):
    """
    MACD-based trading strategy.
    
    This strategy uses MACD (Moving Average Convergence Divergence) to generate
    trading signals. It supports configurable parameters and threshold-based
    signal evaluation.
    """
    
    def __init__(self, 
                 fast_period: int = 7, 
                 slow_period: int = 72, 
                 signal_period: int = 144,
                 name: Optional[str] = None):
        """
        Initialize MACD strategy.
        
        Args:
            fast_period: Fast EMA period (default: 7)
            slow_period: Slow EMA period (default: 72)
            signal_period: Signal line EMA period (default: 144)
            name: Optional strategy name
        """
        super().__init__(name)
        
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        
        # Store parameters
        self.set_parameter('fast_period', fast_period)
        self.set_parameter('slow_period', slow_period)
        self.set_parameter('signal_period', signal_period)
    
    def calculate_signal(self, data: MarketData) -> Optional[Signal]:
        """
        Calculate MACD-based trading signal.
        
        Args:
            data: Market data containing candles
            
        Returns:
            Signal object if a signal is generated, None otherwise
        """
        try:
            # Validate data
            if not self.validate_data(data):
                return None
            
            # Calculate MACD
            macd_values = self._calculate_macd(data.candles['close'])
            
            if macd_values is None or macd_values.empty:
                return None
            
            # Get latest MACD values
            latest = macd_values.iloc[-1]
            
            # Determine signal based on histogram
            signal_type = self._determine_signal_type(latest)
            
            if signal_type is None:
                return None
            
            # Calculate confidence and strength
            confidence = self._calculate_confidence(latest)
            strength = abs(float(latest['hist']))
            
            # Create signal
            signal = Signal(
                symbol=data.symbol,
                signal_type=signal_type,
                confidence=confidence,
                strength=strength,
                timeframe=data.timeframe,
                timestamp=datetime.now(),
                strategy_name=self.get_name(),
                details={
                    'macd': float(latest['macd']),
                    'signal': float(latest['signal']),
                    'hist': float(latest['hist']),
                    'fast_period': self.fast_period,
                    'slow_period': self.slow_period,
                    'signal_period': self.signal_period,
                    'strategy': 'MACD'
                }
            )
            
            # Log signal calculation
            try:
                debug_helper.log_step(
                    f"MACD signal calculated for {data.symbol}",
                    {
                        'signal_type': signal_type,
                        'confidence': confidence,
                        'strength': strength,
                        'macd': float(latest['macd']),
                        'signal': float(latest['signal']),
                        'hist': float(latest['hist'])
                    }
                )
            except Exception:
                pass
            
            return signal
            
        except Exception as e:
            print(f"❌ MACD strategy error for {data.symbol}: {e}")
            return None
    
    def get_name(self) -> str:
        """Get strategy name"""
        return f"MACD_{self.fast_period}_{self.slow_period}_{self.signal_period}"
    
    def get_minimum_data_points(self) -> int:
        """Get minimum data points required for MACD calculation"""
        return max(self.slow_period, self.signal_period) + 10
    
    def _calculate_macd(self, close_prices: pd.Series) -> Optional[pd.DataFrame]:
        """
        Calculate MACD values.
        
        Args:
            close_prices: Series of closing prices
            
        Returns:
            DataFrame with MACD, signal, and histogram values
        """
        try:
            # Use optimized function for default parameters
            if (self.fast_period, self.slow_period, self.signal_period) == (7, 72, 144):
                return compute_macd_772144(close_prices)
            
            # Calculate MACD with custom parameters
            if close_prices is None or len(close_prices) == 0:
                return None
            
            # Ensure we have enough data
            if len(close_prices) < self.get_minimum_data_points():
                return None
            
            # Calculate EMAs
            ema_fast = close_prices.ewm(span=self.fast_period, adjust=False).mean()
            ema_slow = close_prices.ewm(span=self.slow_period, adjust=False).mean()
            
            # Calculate MACD line
            macd_line = ema_fast - ema_slow
            
            # Calculate signal line
            signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()
            
            # Calculate histogram
            histogram = macd_line - signal_line
            
            # Create result DataFrame
            macd_df = pd.DataFrame({
                'macd': macd_line,
                'signal': signal_line,
                'hist': histogram
            })
            
            return macd_df
            
        except Exception as e:
            print(f"❌ MACD calculation error: {e}")
            return None
    
    def _determine_signal_type(self, macd_row: pd.Series) -> Optional[str]:
        """
        Determine signal type based on MACD values.
        
        Args:
            macd_row: Latest MACD values (macd, signal, hist)
            
        Returns:
            'BUY', 'SELL', or None
        """
        try:
            hist = float(macd_row['hist'])
            
            # Simple histogram-based signal
            if hist > 0:
                return 'BUY'
            elif hist < 0:
                return 'SELL'
            else:
                return None
                
        except Exception:
            return None
    
    def _calculate_confidence(self, macd_row: pd.Series) -> float:
        """
        Calculate signal confidence based on MACD values.
        
        Args:
            macd_row: Latest MACD values
            
        Returns:
            Confidence value between 0.0 and 1.0
        """
        try:
            hist = abs(float(macd_row['hist']))
            
            # Simple confidence calculation based on histogram magnitude
            # Normalize to 0-1 range (adjust threshold as needed)
            confidence = min(hist / 10.0, 1.0)
            
            return max(0.0, min(1.0, confidence))
            
        except Exception:
            return 0.5  # Default confidence


class MACDThresholdStrategy(MACDStrategy):
    """
    MACD strategy with configurable thresholds for signal generation.
    
    This strategy extends the basic MACD strategy by using configurable
    thresholds for more precise signal generation.
    """
    
    def __init__(self, 
                 fast_period: int = 7, 
                 slow_period: int = 72, 
                 signal_period: int = 144,
                 thresholds: Optional[Dict[str, float]] = None,
                 name: Optional[str] = None):
        """
        Initialize MACD threshold strategy.
        
        Args:
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period
            thresholds: Dictionary of thresholds for different timeframes
            name: Optional strategy name
        """
        super().__init__(fast_period, slow_period, signal_period, name)
        
        # Default thresholds
        self.thresholds = thresholds or {
            '1m': 0.22,
            '2m': 0.33,
            '5m': 0.47,
            '15m': 0.74,
            '30m': 1.0,
            '1h': 1.47
        }
        
        self.set_parameter('thresholds', self.thresholds)
    
    def _determine_signal_type(self, macd_row: pd.Series) -> Optional[str]:
        """
        Determine signal type using threshold-based logic.
        
        Args:
            macd_row: Latest MACD values
            
        Returns:
            'BUY', 'SELL', or None
        """
        try:
            fmacd = float(macd_row['macd'])
            smacd = float(macd_row['signal'])
            
            # Get threshold for current timeframe (would need to be passed in)
            # For now, use a default threshold
            threshold = 0.33  # Default threshold
            
            # OR logic: BUY if either fmacd or smacd exceeds positive threshold
            if fmacd >= threshold or smacd >= threshold:
                return 'BUY'
            elif fmacd <= -threshold or smacd <= -threshold:
                return 'SELL'
            else:
                return None
                
        except Exception:
            return None
    
    def set_timeframe_threshold(self, timeframe: str, threshold: float):
        """
        Set threshold for a specific timeframe.
        
        Args:
            timeframe: Timeframe (e.g., '1m', '5m', '1h')
            threshold: Threshold value
        """
        self.thresholds[timeframe] = threshold
        self.set_parameter('thresholds', self.thresholds)
    
    def get_threshold(self, timeframe: str) -> float:
        """
        Get threshold for a specific timeframe.
        
        Args:
            timeframe: Timeframe
            
        Returns:
            Threshold value
        """
        return self.thresholds.get(timeframe, 0.33)  # Default threshold
