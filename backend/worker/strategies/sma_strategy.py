"""
SMA Strategy Implementation

This module implements the SMA (Simple Moving Average) trading strategy
with multi-timeframe analysis and signal generation.
"""

from typing import Optional, Dict, Any, List
import pandas as pd
from datetime import datetime
from enum import Enum

from .base_strategy import SignalStrategy, MarketData, Signal
from app.services.sma_indicators import sma_indicator_service
from app.services.sma_signal_engine import sma_signal_engine
from app.services.debug import debug_helper


class SMASignalType(Enum):
    """SMA signal types"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    CONFIRMED_BULLISH = "confirmed_bullish"
    CONFIRMED_BEARISH = "confirmed_bearish"
    TRIPLE_BULLISH = "triple_bullish"
    TRIPLE_BEARISH = "triple_bearish"
    NEUTRAL = "neutral"


class SMAStrategy(SignalStrategy):
    """
    SMA-based trading strategy.
    
    This strategy uses Simple Moving Averages to generate trading signals.
    It supports multiple SMA periods and multi-timeframe analysis.
    """
    
    def __init__(self, 
                 m1_period: int = 18,
                 m2_period: int = 36,
                 m3_period: int = 48,
                 ma144_period: int = 144,
                 name: Optional[str] = None):
        """
        Initialize SMA strategy.
        
        Args:
            m1_period: First SMA period (default: 18)
            m2_period: Second SMA period (default: 36)
            m3_period: Third SMA period (default: 48)
            ma144_period: Long-term SMA period (default: 144)
            name: Optional strategy name
        """
        super().__init__(name)
        
        self.m1_period = m1_period
        self.m2_period = m2_period
        self.m3_period = m3_period
        self.ma144_period = ma144_period
        
        # Store parameters
        self.set_parameter('m1_period', m1_period)
        self.set_parameter('m2_period', m2_period)
        self.set_parameter('m3_period', m3_period)
        self.set_parameter('ma144_period', ma144_period)
    
    def calculate_signal(self, data: MarketData) -> Optional[Signal]:
        """
        Calculate SMA-based trading signal.
        
        Args:
            data: Market data containing candles
            
        Returns:
            Signal object if a signal is generated, None otherwise
        """
        try:
            # Validate data
            if not self.validate_data(data):
                return None
            
            # Calculate SMA indicators
            sma_results = self._calculate_sma_indicators(data.candles)
            
            if not sma_results:
                return None
            
            # Determine signal type
            signal_type = self._determine_signal_type(sma_results)
            
            if signal_type is None or signal_type == SMASignalType.NEUTRAL:
                return None
            
            # Calculate confidence and strength
            confidence = self._calculate_confidence(sma_results, signal_type)
            strength = self._calculate_strength(sma_results, signal_type)
            
            # Map SMA signal type to standard signal type
            standard_signal_type = self._map_sma_signal_type(signal_type)
            
            # Create signal
            signal = Signal(
                symbol=data.symbol,
                signal_type=standard_signal_type,
                confidence=confidence,
                strength=strength,
                timeframe=data.timeframe,
                timestamp=datetime.now(),
                strategy_name=self.get_name(),
                details={
                    'sma_signal_type': signal_type.value,
                    'm1': float(sma_results.get('m1', 0)),
                    'm2': float(sma_results.get('m2', 0)),
                    'm3': float(sma_results.get('m3', 0)),
                    'ma144': float(sma_results.get('ma144', 0)),
                    'avg_m1_m2_m3': float(sma_results.get('avg_m1_m2_m3', 0)),
                    'close': float(data.candles['close'].iloc[-1]),
                    'strategy': 'SMA'
                }
            )
            
            # Log signal calculation
            try:
                debug_helper.log_step(
                    f"SMA signal calculated for {data.symbol}",
                    {
                        'signal_type': signal_type.value,
                        'confidence': confidence,
                        'strength': strength,
                        'm1': float(sma_results.get('m1', 0)),
                        'm2': float(sma_results.get('m2', 0)),
                        'm3': float(sma_results.get('m3', 0)),
                        'ma144': float(sma_results.get('ma144', 0))
                    }
                )
            except Exception:
                pass
            
            return signal
            
        except Exception as e:
            print(f"❌ SMA strategy error for {data.symbol}: {e}")
            return None
    
    def get_name(self) -> str:
        """Get strategy name"""
        return f"SMA_{self.m1_period}_{self.m2_period}_{self.m3_period}_{self.ma144_period}"
    
    def get_minimum_data_points(self) -> int:
        """Get minimum data points required for SMA calculation"""
        return max(self.m1_period, self.m2_period, self.m3_period, self.ma144_period) + 10
    
    def _calculate_sma_indicators(self, candles: pd.DataFrame) -> Optional[Dict[str, float]]:
        """
        Calculate SMA indicators.
        
        Args:
            candles: DataFrame with OHLCV data
            
        Returns:
            Dictionary with SMA values
        """
        try:
            # Use the existing SMA indicator service
            sma_results = sma_indicator_service.calculate_all_smas(candles)
            
            if not sma_results:
                return None
            
            # Get latest values
            latest_values = {}
            for name, series in sma_results.items():
                if not series.empty:
                    latest_values[name] = series.iloc[-1]
                else:
                    latest_values[name] = 0.0
            
            return latest_values
            
        except Exception as e:
            print(f"❌ SMA calculation error: {e}")
            return None
    
    def _determine_signal_type(self, sma_results: Dict[str, float]) -> Optional[SMASignalType]:
        """
        Determine SMA signal type based on SMA values.
        
        Args:
            sma_results: Dictionary with SMA values
            
        Returns:
            SMA signal type or None
        """
        try:
            close = sma_results.get('close', 0)
            m1 = sma_results.get('m1', 0)
            m2 = sma_results.get('m2', 0)
            m3 = sma_results.get('m3', 0)
            ma144 = sma_results.get('ma144', 0)
            avg_m1_m2_m3 = sma_results.get('avg_m1_m2_m3', 0)
            
            # Basic SMA crossover logic
            if close > m1 > m2 > m3 and avg_m1_m2_m3 > ma144:
                return SMASignalType.CONFIRMED_BULLISH
            elif close < m1 < m2 < m3 and avg_m1_m2_m3 < ma144:
                return SMASignalType.CONFIRMED_BEARISH
            elif close > m1 and m1 > m2:
                return SMASignalType.BULLISH
            elif close < m1 and m1 < m2:
                return SMASignalType.BEARISH
            else:
                return SMASignalType.NEUTRAL
                
        except Exception:
            return None
    
    def _map_sma_signal_type(self, sma_signal_type: SMASignalType) -> str:
        """
        Map SMA signal type to standard signal type.
        
        Args:
            sma_signal_type: SMA signal type
            
        Returns:
            Standard signal type ('BUY', 'SELL', 'HOLD')
        """
        if sma_signal_type in [SMASignalType.BULLISH, SMASignalType.CONFIRMED_BULLISH, SMASignalType.TRIPLE_BULLISH]:
            return 'BUY'
        elif sma_signal_type in [SMASignalType.BEARISH, SMASignalType.CONFIRMED_BEARISH, SMASignalType.TRIPLE_BEARISH]:
            return 'SELL'
        else:
            return 'HOLD'
    
    def _calculate_confidence(self, sma_results: Dict[str, float], signal_type: SMASignalType) -> float:
        """
        Calculate signal confidence based on SMA values and signal type.
        
        Args:
            sma_results: Dictionary with SMA values
            signal_type: SMA signal type
            
        Returns:
            Confidence value between 0.0 and 1.0
        """
        try:
            # Base confidence based on signal type
            base_confidence = {
                SMASignalType.BULLISH: 0.6,
                SMASignalType.BEARISH: 0.6,
                SMASignalType.CONFIRMED_BULLISH: 0.8,
                SMASignalType.CONFIRMED_BEARISH: 0.8,
                SMASignalType.TRIPLE_BULLISH: 0.9,
                SMASignalType.TRIPLE_BEARISH: 0.9,
                SMASignalType.NEUTRAL: 0.0
            }
            
            confidence = base_confidence.get(signal_type, 0.5)
            
            # Adjust confidence based on SMA alignment
            close = sma_results.get('close', 0)
            m1 = sma_results.get('m1', 0)
            m2 = sma_results.get('m2', 0)
            m3 = sma_results.get('m3', 0)
            
            if close > 0 and m1 > 0 and m2 > 0 and m3 > 0:
                # Calculate alignment strength
                if signal_type in [SMASignalType.BULLISH, SMASignalType.CONFIRMED_BULLISH, SMASignalType.TRIPLE_BULLISH]:
                    alignment = (close - m3) / close if close > m3 else 0
                else:
                    alignment = (m3 - close) / m3 if m3 > close else 0
                
                # Adjust confidence based on alignment
                confidence += alignment * 0.2
                confidence = min(1.0, confidence)
            
            return max(0.0, min(1.0, confidence))
            
        except Exception:
            return 0.5  # Default confidence
    
    def _calculate_strength(self, sma_results: Dict[str, float], signal_type: SMASignalType) -> float:
        """
        Calculate signal strength based on SMA values.
        
        Args:
            sma_results: Dictionary with SMA values
            signal_type: SMA signal type
            
        Returns:
            Signal strength value
        """
        try:
            close = sma_results.get('close', 0)
            m1 = sma_results.get('m1', 0)
            m2 = sma_results.get('m2', 0)
            m3 = sma_results.get('m3', 0)
            
            if close > 0 and m1 > 0:
                # Calculate strength based on distance from M1
                strength = abs(close - m1) / close
                return min(1.0, strength)
            else:
                return 0.0
                
        except Exception:
            return 0.0


class MultiTimeframeSMAStrategy(SMAStrategy):
    """
    Multi-timeframe SMA strategy.
    
    This strategy extends the basic SMA strategy by analyzing multiple
    timeframes and generating signals based on consensus across timeframes.
    """
    
    def __init__(self, 
                 timeframes: List[str] = None,
                 m1_period: int = 18,
                 m2_period: int = 36,
                 m3_period: int = 48,
                 ma144_period: int = 144,
                 name: Optional[str] = None):
        """
        Initialize multi-timeframe SMA strategy.
        
        Args:
            timeframes: List of timeframes to analyze
            m1_period: First SMA period
            m2_period: Second SMA period
            m3_period: Third SMA period
            ma144_period: Long-term SMA period
            name: Optional strategy name
        """
        super().__init__(m1_period, m2_period, m3_period, ma144_period, name)
        
        self.timeframes = timeframes or ['1m', '2m', '5m', '15m', '30m', '1h']
        self.set_parameter('timeframes', self.timeframes)
    
    def calculate_multi_timeframe_signal(self, market_data_map: Dict[str, MarketData]) -> Optional[Signal]:
        """
        Calculate signal based on multiple timeframes.
        
        Args:
            market_data_map: Dictionary mapping timeframe to MarketData
            
        Returns:
            Signal object if consensus is reached, None otherwise
        """
        try:
            timeframe_signals = {}
            
            # Calculate signal for each timeframe
            for timeframe, data in market_data_map.items():
                if timeframe in self.timeframes:
                    signal = self.calculate_signal(data)
                    if signal:
                        timeframe_signals[timeframe] = signal
            
            if not timeframe_signals:
                return None
            
            # Analyze consensus
            consensus_signal = self._analyze_consensus(timeframe_signals)
            
            if consensus_signal:
                # Create multi-timeframe signal
                multi_signal = Signal(
                    symbol=list(timeframe_signals.values())[0].symbol,
                    signal_type=consensus_signal.signal_type,
                    confidence=consensus_signal.confidence,
                    strength=consensus_signal.strength,
                    timeframe='multi',
                    timestamp=datetime.now(),
                    strategy_name=f"{self.get_name()}_Multi",
                    details={
                        'timeframe_signals': {
                            tf: {
                                'signal_type': sig.signal_type,
                                'confidence': sig.confidence,
                                'strength': sig.strength
                            } for tf, sig in timeframe_signals.items()
                        },
                        'consensus_count': len(timeframe_signals),
                        'strategy': 'MultiTimeframeSMA'
                    }
                )
                
                return multi_signal
            
            return None
            
        except Exception as e:
            print(f"❌ Multi-timeframe SMA strategy error: {e}")
            return None
    
    def _analyze_consensus(self, timeframe_signals: Dict[str, Signal]) -> Optional[Signal]:
        """
        Analyze consensus across timeframes.
        
        Args:
            timeframe_signals: Dictionary mapping timeframe to Signal
            
        Returns:
            Consensus signal or None
        """
        try:
            if len(timeframe_signals) < 3:  # Need at least 3 timeframes for consensus
                return None
            
            # Count signals by type
            buy_count = sum(1 for sig in timeframe_signals.values() if sig.signal_type == 'BUY')
            sell_count = sum(1 for sig in timeframe_signals.values() if sig.signal_type == 'SELL')
            
            total_signals = len(timeframe_signals)
            
            # Require at least 60% consensus
            min_consensus = int(total_signals * 0.6)
            
            if buy_count >= min_consensus:
                # Calculate average confidence and strength for BUY signals
                buy_signals = [sig for sig in timeframe_signals.values() if sig.signal_type == 'BUY']
                avg_confidence = sum(sig.confidence for sig in buy_signals) / len(buy_signals)
                avg_strength = sum(sig.strength for sig in buy_signals) / len(buy_signals)
                
                return Signal(
                    symbol=buy_signals[0].symbol,
                    signal_type='BUY',
                    confidence=avg_confidence,
                    strength=avg_strength,
                    timeframe='multi',
                    timestamp=datetime.now(),
                    strategy_name=self.get_name(),
                    details={'consensus_type': 'buy', 'consensus_count': buy_count}
                )
            
            elif sell_count >= min_consensus:
                # Calculate average confidence and strength for SELL signals
                sell_signals = [sig for sig in timeframe_signals.values() if sig.signal_type == 'SELL']
                avg_confidence = sum(sig.confidence for sig in sell_signals) / len(sell_signals)
                avg_strength = sum(sig.strength for sig in sell_signals) / len(sell_signals)
                
                return Signal(
                    symbol=sell_signals[0].symbol,
                    signal_type='SELL',
                    confidence=avg_confidence,
                    strength=avg_strength,
                    timeframe='multi',
                    timestamp=datetime.now(),
                    strategy_name=self.get_name(),
                    details={'consensus_type': 'sell', 'consensus_count': sell_count}
                )
            
            return None
            
        except Exception:
            return None
