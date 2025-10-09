"""
Indicator Calculation Step

This module implements indicator calculation step for the processing pipeline.
"""

from typing import Optional, Dict, Any
import pandas as pd

from .base_pipeline import ProcessingStep
from ..strategies.base_strategy import MarketData
from app.services.debug import debug_helper


class IndicatorCalculationStep(ProcessingStep):
    """
    Indicator calculation step for the processing pipeline.
    
    This step calculates technical indicators based on market data
    and stores the results for use by subsequent steps.
    """
    
    def __init__(self, 
                 indicator_types: Optional[list] = None,
                 name: Optional[str] = None):
        """
        Initialize indicator calculation step.
        
        Args:
            indicator_types: List of indicator types to calculate
            name: Optional step name
        """
        super().__init__(name)
        
        self.indicator_types = indicator_types or ['macd', 'sma']
        self.set_parameter('indicator_types', self.indicator_types)
    
    def process(self, data: MarketData) -> MarketData:
        """
        Calculate technical indicators.
        
        Args:
            data: Input market data
            
        Returns:
            Market data with calculated indicators
            
        Raises:
            ValueError: If indicator calculation fails
        """
        try:
            # Log calculation start
            debug_helper.log_step(
                f"Indicator calculation for {data.symbol}",
                {
                    'indicator_types': self.indicator_types,
                    'candles_count': len(data.candles)
                }
            )
            
            # Initialize indicators dictionary in metadata
            if data.metadata is None:
                data.metadata = {}
            
            if 'indicators' not in data.metadata:
                data.metadata['indicators'] = {}
            
            # Calculate each indicator type
            for indicator_type in self.indicator_types:
                try:
                    indicators = self._calculate_indicator(data.candles, indicator_type)
                    if indicators is not None:
                        data.metadata['indicators'][indicator_type] = indicators
                        
                        debug_helper.log_step(
                            f"Calculated {indicator_type} for {data.symbol}",
                            {
                                'indicator_type': indicator_type,
                                'values_count': len(indicators) if isinstance(indicators, dict) else 0
                            }
                        )
                    else:
                        debug_helper.log_step(
                            f"Failed to calculate {indicator_type} for {data.symbol}",
                            {'indicator_type': indicator_type}
                        )
                        
                except Exception as e:
                    debug_helper.log_step(
                        f"Error calculating {indicator_type} for {data.symbol}",
                        error=e
                    )
                    # Continue with other indicators even if one fails
                    continue
            
            # Log successful calculation
            debug_helper.log_step(
                f"Indicator calculation completed for {data.symbol}",
                {
                    'calculated_indicators': list(data.metadata['indicators'].keys()),
                    'total_indicators': len(data.metadata['indicators'])
                }
            )
            
            return data
            
        except Exception as e:
            error_msg = f"Indicator calculation failed for {data.symbol}: {str(e)}"
            debug_helper.log_step(f"Indicator calculation error for {data.symbol}", error=e)
            raise ValueError(error_msg)
    
    def get_name(self) -> str:
        """Get step name"""
        return "IndicatorCalculation"
    
    def _calculate_indicator(self, candles: pd.DataFrame, indicator_type: str) -> Optional[Dict[str, Any]]:
        """
        Calculate a specific indicator.
        
        Args:
            candles: DataFrame with OHLCV data
            indicator_type: Type of indicator to calculate
            
        Returns:
            Dictionary with indicator values or None if calculation fails
        """
        try:
            if indicator_type == 'macd':
                return self._calculate_macd(candles)
            elif indicator_type == 'sma':
                return self._calculate_sma(candles)
            elif indicator_type == 'rsi':
                return self._calculate_rsi(candles)
            elif indicator_type == 'bollinger':
                return self._calculate_bollinger_bands(candles)
            else:
                print(f"⚠️ Unknown indicator type: {indicator_type}")
                return None
                
        except Exception as e:
            print(f"❌ Error calculating {indicator_type}: {e}")
            return None
    
    def _calculate_macd(self, candles: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Calculate MACD indicator.
        
        Args:
            candles: DataFrame with OHLCV data
            
        Returns:
            Dictionary with MACD values
        """
        try:
            from app.services.indicators import compute_macd_772144
            
            close_prices = candles['close']
            macd_df = compute_macd_772144(close_prices)
            
            if macd_df is None or macd_df.empty:
                return None
            
            # Get latest values
            latest = macd_df.iloc[-1]
            
            return {
                'macd': float(latest['macd']),
                'signal': float(latest['signal']),
                'histogram': float(latest['hist']),
                'macd_line': macd_df['macd'].tolist(),
                'signal_line': macd_df['signal'].tolist(),
                'histogram_line': macd_df['hist'].tolist()
            }
            
        except Exception as e:
            print(f"❌ MACD calculation error: {e}")
            return None
    
    def _calculate_sma(self, candles: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Calculate SMA indicators.
        
        Args:
            candles: DataFrame with OHLCV data
            
        Returns:
            Dictionary with SMA values
        """
        try:
            from app.services.sma_indicators import sma_indicator_service
            
            sma_results = sma_indicator_service.calculate_all_smas(candles)
            
            if not sma_results:
                return None
            
            # Get latest values
            latest_values = {}
            for name, series in sma_results.items():
                if not series.empty:
                    latest_values[name] = float(series.iloc[-1])
                else:
                    latest_values[name] = 0.0
            
            return latest_values
            
        except Exception as e:
            print(f"❌ SMA calculation error: {e}")
            return None
    
    def _calculate_rsi(self, candles: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Calculate RSI indicator.
        
        Args:
            candles: DataFrame with OHLCV data
            
        Returns:
            Dictionary with RSI values
        """
        try:
            close_prices = candles['close']
            
            # Calculate price changes
            delta = close_prices.diff()
            
            # Separate gains and losses
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)
            
            # Calculate average gains and losses (14-period)
            avg_gains = gains.rolling(window=14).mean()
            avg_losses = losses.rolling(window=14).mean()
            
            # Calculate RSI
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))
            
            if rsi.empty or rsi.isna().all():
                return None
            
            latest_rsi = float(rsi.iloc[-1])
            
            return {
                'rsi': latest_rsi,
                'rsi_line': rsi.tolist(),
                'overbought': latest_rsi > 70,
                'oversold': latest_rsi < 30
            }
            
        except Exception as e:
            print(f"❌ RSI calculation error: {e}")
            return None
    
    def _calculate_bollinger_bands(self, candles: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Calculate Bollinger Bands indicator.
        
        Args:
            candles: DataFrame with OHLCV data
            
        Returns:
            Dictionary with Bollinger Bands values
        """
        try:
            close_prices = candles['close']
            
            # Calculate SMA (20-period)
            sma = close_prices.rolling(window=20).mean()
            
            # Calculate standard deviation
            std = close_prices.rolling(window=20).std()
            
            # Calculate bands
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)
            
            if sma.empty or sma.isna().all():
                return None
            
            latest_close = float(close_prices.iloc[-1])
            latest_upper = float(upper_band.iloc[-1])
            latest_middle = float(sma.iloc[-1])
            latest_lower = float(lower_band.iloc[-1])
            
            return {
                'upper_band': latest_upper,
                'middle_band': latest_middle,
                'lower_band': latest_lower,
                'current_price': latest_close,
                'upper_band_line': upper_band.tolist(),
                'middle_band_line': sma.tolist(),
                'lower_band_line': lower_band.tolist(),
                'above_upper': latest_close > latest_upper,
                'below_lower': latest_close < latest_lower
            }
            
        except Exception as e:
            print(f"❌ Bollinger Bands calculation error: {e}")
            return None
    
    def set_indicator_types(self, indicator_types: list) -> None:
        """
        Set indicator types to calculate.
        
        Args:
            indicator_types: List of indicator types
        """
        self.indicator_types = indicator_types
        self.set_parameter('indicator_types', indicator_types)
    
    def add_indicator_type(self, indicator_type: str) -> None:
        """
        Add an indicator type to calculate.
        
        Args:
            indicator_type: Indicator type to add
        """
        if indicator_type not in self.indicator_types:
            self.indicator_types.append(indicator_type)
            self.set_parameter('indicator_types', self.indicator_types)
    
    def remove_indicator_type(self, indicator_type: str) -> None:
        """
        Remove an indicator type.
        
        Args:
            indicator_type: Indicator type to remove
        """
        if indicator_type in self.indicator_types:
            self.indicator_types.remove(indicator_type)
            self.set_parameter('indicator_types', self.indicator_types)
