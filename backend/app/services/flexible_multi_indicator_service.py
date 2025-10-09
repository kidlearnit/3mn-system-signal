"""
Flexible Multi-Indicator Service
Handles dynamic multi-indicator analysis and signal generation
"""

import logging
from typing import Dict, List, Any, Optional
from app.services.indicators import compute_macd, compute_sma, compute_rsi, compute_bollinger_bands
from app.services.aggregation_engine import AggregationEngine
from app.services.strategy_base import SignalResult
from app.services.data_fetcher import DataFetcher
import pandas as pd
import numpy as np
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class FlexibleMultiIndicatorService:
    """Service for flexible multi-indicator analysis"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.aggregation_engine = AggregationEngine()
        self.available_indicators = {
            'macd_multi': {
                'name': 'MACD Multi-TF',
                'icon': 'fas fa-chart-line',
                'weight': 0.3,
                'analyzer': self._analyze_macd_multi
            },
            'sma': {
                'name': 'SMA',
                'icon': 'fas fa-chart-area',
                'weight': 0.25,
                'analyzer': self._analyze_sma
            },
            'rsi': {
                'name': 'RSI',
                'icon': 'fas fa-chart-bar',
                'weight': 0.2,
                'analyzer': self._analyze_rsi
            },
            'bollinger': {
                'name': 'Bollinger Bands',
                'icon': 'fas fa-chart-pie',
                'weight': 0.25,
                'analyzer': self._analyze_bollinger
            }
        }
    
    def get_available_indicators(self) -> Dict[str, Any]:
        """Get list of available indicators"""
        return self.available_indicators
    
    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate flexible multi-indicator configuration"""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ['symbols', 'symbolConfigs', 'aggregation']
        for field in required_fields:
            if field not in config:
                errors.append(f'Missing required field: {field}')
        
        if errors:
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        symbols = config.get('symbols', [])
        symbol_configs = config.get('symbolConfigs', {})
        aggregation = config.get('aggregation', {})
        
        # Validate symbols
        if not symbols:
            errors.append('No symbols configured')
        
        # Validate symbol configurations
        for symbol in symbols:
            if symbol not in symbol_configs:
                errors.append(f'Configuration missing for symbol: {symbol}')
                continue
            
            symbol_config = symbol_configs[symbol]
            indicators = symbol_config.get('indicators', [])
            
            if not indicators:
                errors.append(f'No indicators configured for symbol: {symbol}')
                continue
            
            # Check minimum indicators requirement
            min_indicators = aggregation.get('minIndicators', 3)
            if len(indicators) < min_indicators:
                errors.append(f'Symbol {symbol} has only {len(indicators)} indicators, minimum {min_indicators} required')
            
            # Validate indicator types
            for indicator in indicators:
                indicator_type = indicator.get('type')
                if indicator_type not in self.available_indicators:
                    errors.append(f'Unknown indicator type: {indicator_type} for symbol: {symbol}')
        
        # Validate aggregation settings
        method = aggregation.get('method', 'weighted_average')
        valid_methods = ['weighted_average', 'majority_vote', 'consensus']
        if method not in valid_methods:
            errors.append(f'Invalid aggregation method: {method}')
        
        # Check thresholds
        consensus_threshold = aggregation.get('consensusThreshold', 0.7)
        if not 0.5 <= consensus_threshold <= 1.0:
            warnings.append(f'Consensus threshold {consensus_threshold} is outside recommended range [0.5, 1.0]')
        
        confidence_threshold = aggregation.get('confidenceThreshold', 0.6)
        if not 0.3 <= confidence_threshold <= 1.0:
            warnings.append(f'Confidence threshold {confidence_threshold} is outside recommended range [0.3, 1.0]')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def execute_workflow(self, symbols: List[str], symbol_configs: Dict[str, Any], 
                        aggregation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute flexible multi-indicator workflow"""
        results = []
        
        for symbol in symbols:
            try:
                # Get symbol configuration
                symbol_config = symbol_configs.get(symbol, {})
                indicators = symbol_config.get('indicators', [])
                
                if not indicators:
                    logger.warning(f'No indicators configured for symbol: {symbol}')
                    continue
                
                # Analyze symbol with all configured indicators
                symbol_result = self.analyze_symbol(symbol, indicators)
                
                # Aggregate signals
                if symbol_result.get('signals'):
                    # Convert dict signals to SignalResult objects for aggregation
                    signal_objects = []
                    for signal_dict in symbol_result['signals']:
                        signal_obj = SignalResult(
                            strategy_name=signal_dict['type'],
                            direction=signal_dict['signal_type'],
                            strength=signal_dict['confidence'],
                            signal_type=signal_dict['signal_type'],
                            confidence=signal_dict['confidence'],
                            details=signal_dict['details'],
                            timestamp=datetime.now(timezone.utc),
                            timeframe='1h',
                            symbol_id=0,  # Placeholder
                            ticker=symbol,
                            exchange='US'
                        )
                        signal_objects.append(signal_obj)
                    
                    aggregated_signal = self.aggregation_engine.aggregate_signals(
                        signal_objects,
                        aggregation.get('method', 'weighted_average'),
                        {ind['type']: ind.get('weight', 0.25) for ind in indicators},
                        '1h',  # Default timeframe
                        {
                            'consensus_threshold': aggregation.get('consensusThreshold', 0.7),
                            'confidence_threshold': aggregation.get('confidenceThreshold', 0.6),
                            'min_indicators': aggregation.get('minIndicators', 3)
                        }
                    )
                    
                    symbol_result['aggregated_signal'] = aggregated_signal
                
                results.append(symbol_result)
                
            except Exception as e:
                logger.error(f'Error processing symbol {symbol}: {str(e)}')
                results.append({
                    'symbol': symbol,
                    'error': str(e),
                    'signals': [],
                    'aggregated_signal': None
                })
        
        return results
    
    def analyze_symbol(self, symbol: str, indicators: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze a single symbol with configured indicators"""
        try:
            # Fetch data for symbol
            data = self.data_fetcher.fetch_symbol_data(symbol, '1y')
            if data is None or data.empty:
                return {
                    'symbol': symbol,
                    'error': 'No data available',
                    'signals': [],
                    'aggregated_signal': None
                }
            
            signals = []
            
            # Analyze each indicator
            for indicator_config in indicators:
                indicator_type = indicator_config.get('type')
                weight = indicator_config.get('weight', 0.25)
                config = indicator_config.get('config', {})
                
                if indicator_type not in self.available_indicators:
                    logger.warning(f'Unknown indicator type: {indicator_type}')
                    continue
                
                try:
                    # Get analyzer function
                    analyzer = self.available_indicators[indicator_type]['analyzer']
                    
                    # Analyze indicator
                    signal = analyzer(symbol, data, config, weight)
                    
                    if signal:
                        signals.append(signal)
                        
                except Exception as e:
                    logger.error(f'Error analyzing {indicator_type} for {symbol}: {str(e)}')
                    continue
            
            return {
                'symbol': symbol,
                'signals': signals,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f'Error analyzing symbol {symbol}: {str(e)}')
            return {
                'symbol': symbol,
                'error': str(e),
                'signals': [],
                'aggregated_signal': None
            }
    
    def _analyze_macd_multi(self, symbol: str, data: pd.DataFrame, 
                           config: Dict[str, Any], weight: float) -> Optional[Dict[str, Any]]:
        """Analyze MACD Multi-Timeframe"""
        try:
            timeframes = config.get('timeframes', ['1m', '2m', '5m', '15m', '30m', '1h'])
            fast_period = config.get('fastPeriod', 7)
            slow_period = config.get('slowPeriod', 113)
            signal_period = config.get('signalPeriod', 144)
            
            # For now, use daily data as proxy for multi-timeframe
            # In production, you would fetch actual multi-timeframe data
            macd_data = compute_macd(data)
            
            if macd_data is None or macd_data.empty:
                return None
            
            # Get latest values
            latest = macd_data.iloc[-1]
            fast_macd = latest.get('macd', 0)
            signal_macd = latest.get('signal', 0)
            
            # Determine signal
            signal_type = 'NEUTRAL'
            confidence = 0.5
            
            if fast_macd > signal_macd and fast_macd > 0:
                signal_type = 'BULL'
                confidence = min(0.9, abs(fast_macd) * 10)
            elif fast_macd < signal_macd and fast_macd < 0:
                signal_type = 'BEAR'
                confidence = min(0.9, abs(fast_macd) * 10)
            
            return {
                'type': 'macd_multi',
                'signal_type': signal_type,
                'confidence': confidence,
                'weight': weight,
                'details': {
                    'fast_macd': fast_macd,
                    'signal_macd': signal_macd,
                    'timeframes': timeframes
                }
            }
            
        except Exception as e:
            logger.error(f'Error analyzing MACD Multi-TF for {symbol}: {str(e)}')
            return None
    
    def _analyze_sma(self, symbol: str, data: pd.DataFrame, 
                    config: Dict[str, Any], weight: float) -> Optional[Dict[str, Any]]:
        """Analyze Simple Moving Average"""
        try:
            periods = config.get('periods', [5, 10, 20, 50, 100, 200])
            timeframes = config.get('timeframes', ['1m', '2m', '5m', '15m', '30m', '1h', '4h'])
            
            # Calculate SMAs
            sma_values = {}
            for period in periods:
                sma_values[period] = compute_sma(data['Close'], period)
            
            # Get latest values
            latest_price = data['Close'].iloc[-1]
            sma_signals = []
            
            for period, sma in sma_values.items():
                if sma is not None and not sma.empty:
                    latest_sma = sma.iloc[-1]
                    if latest_price > latest_sma:
                        sma_signals.append('BULL')
                    elif latest_price < latest_sma:
                        sma_signals.append('BEAR')
                    else:
                        sma_signals.append('NEUTRAL')
            
            # Determine overall signal
            bull_count = sma_signals.count('BULL')
            bear_count = sma_signals.count('BEAR')
            total_count = len(sma_signals)
            
            signal_type = 'NEUTRAL'
            confidence = 0.5
            
            if bull_count > bear_count:
                signal_type = 'BULL'
                confidence = bull_count / total_count
            elif bear_count > bull_count:
                signal_type = 'BEAR'
                confidence = bear_count / total_count
            
            return {
                'type': 'sma',
                'signal_type': signal_type,
                'confidence': confidence,
                'weight': weight,
                'details': {
                    'sma_signals': sma_signals,
                    'periods': periods,
                    'timeframes': timeframes
                }
            }
            
        except Exception as e:
            logger.error(f'Error analyzing SMA for {symbol}: {str(e)}')
            return None
    
    def _analyze_rsi(self, symbol: str, data: pd.DataFrame, 
                    config: Dict[str, Any], weight: float) -> Optional[Dict[str, Any]]:
        """Analyze Relative Strength Index"""
        try:
            period = config.get('period', 14)
            overbought = config.get('overbought', 70)
            oversold = config.get('oversold', 30)
            timeframes = config.get('timeframes', ['5m', '15m', '30m', '1h', '4h'])
            
            # Calculate RSI
            rsi = compute_rsi(data['Close'], period)
            
            if rsi is None or rsi.empty:
                return None
            
            # Get latest value
            latest_rsi = rsi.iloc[-1]
            
            # Determine signal
            signal_type = 'NEUTRAL'
            confidence = 0.5
            
            if latest_rsi > overbought:
                signal_type = 'BEAR'  # Overbought, expect price to fall
                confidence = min(0.9, (latest_rsi - overbought) / (100 - overbought))
            elif latest_rsi < oversold:
                signal_type = 'BULL'  # Oversold, expect price to rise
                confidence = min(0.9, (oversold - latest_rsi) / oversold)
            
            return {
                'type': 'rsi',
                'signal_type': signal_type,
                'confidence': confidence,
                'weight': weight,
                'details': {
                    'rsi_value': latest_rsi,
                    'overbought': overbought,
                    'oversold': oversold,
                    'timeframes': timeframes
                }
            }
            
        except Exception as e:
            logger.error(f'Error analyzing RSI for {symbol}: {str(e)}')
            return None
    
    def _analyze_bollinger(self, symbol: str, data: pd.DataFrame, 
                          config: Dict[str, Any], weight: float) -> Optional[Dict[str, Any]]:
        """Analyze Bollinger Bands"""
        try:
            period = config.get('period', 20)
            std_dev = config.get('stdDev', 2)
            timeframes = config.get('timeframes', ['15m', '30m', '1h', '4h'])
            
            # Calculate Bollinger Bands
            bb_data = compute_bollinger_bands(data, period, std_dev)
            
            if bb_data is None or bb_data.empty:
                return None
            
            # Get latest values
            latest = bb_data.iloc[-1]
            upper = latest['upper']
            middle = latest['middle']
            lower = latest['lower']
            current_price = data['Close'].iloc[-1]
            
            # Determine signal
            signal_type = 'NEUTRAL'
            confidence = 0.5
            
            if current_price > upper:
                signal_type = 'BEAR'  # Price above upper band, expect reversion
                confidence = min(0.9, (current_price - upper) / (upper - middle))
            elif current_price < lower:
                signal_type = 'BULL'  # Price below lower band, expect reversion
                confidence = min(0.9, (lower - current_price) / (middle - lower))
            elif current_price > middle:
                signal_type = 'BULL'  # Price above middle, bullish
                confidence = 0.6
            elif current_price < middle:
                signal_type = 'BEAR'  # Price below middle, bearish
                confidence = 0.6
            
            return {
                'type': 'bollinger',
                'signal_type': signal_type,
                'confidence': confidence,
                'weight': weight,
                'details': {
                    'upper': upper,
                    'middle': middle,
                    'lower': lower,
                    'current_price': current_price,
                    'timeframes': timeframes
                }
            }
            
        except Exception as e:
            logger.error(f'Error analyzing Bollinger Bands for {symbol}: {str(e)}')
            return None
