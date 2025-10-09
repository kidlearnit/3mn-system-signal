"""
Signal Evaluation Step

This module implements signal evaluation step for the processing pipeline.
"""

from typing import Optional, List
import pandas as pd

from .base_pipeline import ProcessingStep
from ..strategies.base_strategy import MarketData, Signal
from ..strategies.macd_strategy import MACDStrategy
from ..strategies.sma_strategy import SMAStrategy
from app.services.debug import debug_helper


class SignalEvaluationStep(ProcessingStep):
    """
    Signal evaluation step for the processing pipeline.
    
    This step evaluates trading signals based on calculated indicators
    and market data using configured strategies.
    """
    
    def __init__(self, 
                 strategies: Optional[List] = None,
                 name: Optional[str] = None):
        """
        Initialize signal evaluation step.
        
        Args:
            strategies: List of signal strategies to use
            name: Optional step name
        """
        super().__init__(name)
        
        self.strategies = strategies or []
        self.set_parameter('strategies', [strategy.get_name() for strategy in self.strategies])
    
    def process(self, data: MarketData) -> MarketData:
        """
        Evaluate trading signals using configured strategies.
        
        Args:
            data: Input market data with calculated indicators
            
        Returns:
            Market data with generated signals
            
        Raises:
            ValueError: If signal evaluation fails
        """
        try:
            # Log evaluation start
            debug_helper.log_step(
                f"Signal evaluation for {data.symbol}",
                {
                    'strategies_count': len(self.strategies),
                    'strategy_names': [strategy.get_name() for strategy in self.strategies]
                }
            )
            
            # Initialize signals list in metadata
            if data.metadata is None:
                data.metadata = {}
            
            if 'signals' not in data.metadata:
                data.metadata['signals'] = []
            
            # Evaluate signals using each strategy
            generated_signals = []
            
            for strategy in self.strategies:
                try:
                    signal = strategy.calculate_signal(data)
                    if signal:
                        generated_signals.append(signal)
                        data.metadata['signals'].append(signal)
                        
                        debug_helper.log_step(
                            f"Generated signal for {data.symbol} using {strategy.get_name()}",
                            {
                                'signal_type': signal.signal_type,
                                'confidence': signal.confidence,
                                'strength': signal.strength
                            }
                        )
                    else:
                        debug_helper.log_step(
                            f"No signal generated for {data.symbol} using {strategy.get_name()}"
                        )
                        
                except Exception as e:
                    debug_helper.log_step(
                        f"Error evaluating signal for {data.symbol} using {strategy.get_name()}",
                        error=e
                    )
                    # Continue with other strategies even if one fails
                    continue
            
            # Log evaluation results
            debug_helper.log_step(
                f"Signal evaluation completed for {data.symbol}",
                {
                    'total_signals': len(generated_signals),
                    'signal_types': [signal.signal_type for signal in generated_signals],
                    'strategies_used': len(self.strategies)
                }
            )
            
            # Add signals to data object for pipeline
            data.signals = generated_signals
            
            return data
            
        except Exception as e:
            error_msg = f"Signal evaluation failed for {data.symbol}: {str(e)}"
            debug_helper.log_step(f"Signal evaluation error for {data.symbol}", error=e)
            raise ValueError(error_msg)
    
    def get_name(self) -> str:
        """Get step name"""
        return "SignalEvaluation"
    
    def add_strategy(self, strategy) -> None:
        """
        Add a signal strategy.
        
        Args:
            strategy: Signal strategy to add
        """
        if strategy not in self.strategies:
            self.strategies.append(strategy)
            self.set_parameter('strategies', [strategy.get_name() for strategy in self.strategies])
    
    def remove_strategy(self, strategy_name: str) -> bool:
        """
        Remove a signal strategy by name.
        
        Args:
            strategy_name: Name of the strategy to remove
            
        Returns:
            True if strategy was removed, False if not found
        """
        for i, strategy in enumerate(self.strategies):
            if strategy.get_name() == strategy_name:
                del self.strategies[i]
                self.set_parameter('strategies', [strategy.get_name() for strategy in self.strategies])
                return True
        return False
    
    def get_strategies(self) -> List:
        """
        Get list of configured strategies.
        
        Returns:
            List of signal strategies
        """
        return self.strategies.copy()
    
    def set_strategies(self, strategies: List) -> None:
        """
        Set the list of strategies.
        
        Args:
            strategies: List of signal strategies
        """
        self.strategies = strategies
        self.set_parameter('strategies', [strategy.get_name() for strategy in self.strategies])


class MultiTimeframeSignalEvaluationStep(SignalEvaluationStep):
    """
    Multi-timeframe signal evaluation step.
    
    This step evaluates signals across multiple timeframes and generates
    consensus signals based on agreement across timeframes.
    """
    
    def __init__(self, 
                 strategies: Optional[List] = None,
                 consensus_threshold: float = 0.6,
                 name: Optional[str] = None):
        """
        Initialize multi-timeframe signal evaluation step.
        
        Args:
            strategies: List of signal strategies to use
            consensus_threshold: Minimum consensus threshold (0.0 to 1.0)
            name: Optional step name
        """
        super().__init__(strategies, name)
        
        self.consensus_threshold = consensus_threshold
        self.set_parameter('consensus_threshold', consensus_threshold)
    
    def process(self, data: MarketData) -> MarketData:
        """
        Evaluate signals across multiple timeframes and generate consensus.
        
        Args:
            data: Input market data (should contain multiple timeframes)
            
        Returns:
            Market data with consensus signals
        """
        try:
            # Check if data contains multiple timeframes
            if not hasattr(data, 'timeframes') or not data.timeframes:
                # Fall back to single timeframe evaluation
                return super().process(data)
            
            # Log multi-timeframe evaluation start
            debug_helper.log_step(
                f"Multi-timeframe signal evaluation for {data.symbol}",
                {
                    'timeframes': data.timeframes,
                    'strategies_count': len(self.strategies),
                    'consensus_threshold': self.consensus_threshold
                }
            )
            
            # Evaluate signals for each timeframe
            timeframe_signals = {}
            
            for timeframe in data.timeframes:
                try:
                    # Create market data for this timeframe
                    tf_data = MarketData(
                        symbol=data.symbol,
                        exchange=data.exchange,
                        timeframe=timeframe,
                        candles=data.timeframe_candles.get(timeframe),
                        timestamp=data.timestamp,
                        metadata=data.metadata
                    )
                    
                    # Evaluate signals for this timeframe
                    tf_data = super().process(tf_data)
                    
                    if tf_data.signals:
                        timeframe_signals[timeframe] = tf_data.signals
                        
                except Exception as e:
                    debug_helper.log_step(
                        f"Error evaluating signals for {data.symbol} {timeframe}",
                        error=e
                    )
                    continue
            
            # Generate consensus signals
            consensus_signals = self._generate_consensus_signals(timeframe_signals)
            
            # Add consensus signals to data
            if data.metadata is None:
                data.metadata = {}
            
            data.metadata['timeframe_signals'] = timeframe_signals
            data.metadata['consensus_signals'] = consensus_signals
            data.signals = consensus_signals
            
            # Log consensus results
            debug_helper.log_step(
                f"Multi-timeframe consensus completed for {data.symbol}",
                {
                    'timeframes_evaluated': len(timeframe_signals),
                    'consensus_signals': len(consensus_signals),
                    'consensus_threshold': self.consensus_threshold
                }
            )
            
            return data
            
        except Exception as e:
            error_msg = f"Multi-timeframe signal evaluation failed for {data.symbol}: {str(e)}"
            debug_helper.log_step(f"Multi-timeframe signal evaluation error for {data.symbol}", error=e)
            raise ValueError(error_msg)
    
    def _generate_consensus_signals(self, timeframe_signals: dict) -> List[Signal]:
        """
        Generate consensus signals from timeframe signals.
        
        Args:
            timeframe_signals: Dictionary mapping timeframe to signals
            
        Returns:
            List of consensus signals
        """
        try:
            if not timeframe_signals:
                return []
            
            # Count signals by type
            signal_counts = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
            total_signals = 0
            
            for timeframe, signals in timeframe_signals.items():
                for signal in signals:
                    signal_counts[signal.signal_type] += 1
                    total_signals += 1
            
            if total_signals == 0:
                return []
            
            # Calculate consensus
            consensus_signals = []
            
            for signal_type, count in signal_counts.items():
                if signal_type == 'HOLD':
                    continue
                
                consensus_ratio = count / total_signals
                
                if consensus_ratio >= self.consensus_threshold:
                    # Create consensus signal
                    consensus_signal = Signal(
                        symbol=list(timeframe_signals.values())[0][0].symbol,
                        signal_type=signal_type,
                        confidence=consensus_ratio,
                        strength=consensus_ratio,
                        timeframe='multi',
                        timestamp=pd.Timestamp.now(),
                        strategy_name=f"MultiTimeframe_{self.get_name()}",
                        details={
                            'consensus_ratio': consensus_ratio,
                            'signal_count': count,
                            'total_signals': total_signals,
                            'timeframes': list(timeframe_signals.keys())
                        }
                    )
                    
                    consensus_signals.append(consensus_signal)
            
            return consensus_signals
            
        except Exception as e:
            print(f"❌ Error generating consensus signals: {e}")
            return []
    
    def set_consensus_threshold(self, threshold: float) -> None:
        """
        Set consensus threshold.
        
        Args:
            threshold: Consensus threshold (0.0 to 1.0)
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Consensus threshold must be between 0.0 and 1.0")
        
        self.consensus_threshold = threshold
        self.set_parameter('consensus_threshold', threshold)
