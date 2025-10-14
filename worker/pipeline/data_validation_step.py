"""
Data Validation Step

This module implements data validation step for the processing pipeline.
"""

from typing import Optional
import pandas as pd

from .base_pipeline import ProcessingStep
from ..strategies.base_strategy import MarketData
from app.services.debug import debug_helper


class DataValidationStep(ProcessingStep):
    """
    Data validation step for the processing pipeline.
    
    This step validates that market data meets the requirements for
    further processing, including data completeness and format validation.
    """
    
    def __init__(self, 
                 min_candles: int = 50,
                 required_columns: Optional[list] = None,
                 name: Optional[str] = None):
        """
        Initialize data validation step.
        
        Args:
            min_candles: Minimum number of candles required
            required_columns: List of required columns
            name: Optional step name
        """
        super().__init__(name)
        
        self.min_candles = min_candles
        self.required_columns = required_columns or ['open', 'high', 'low', 'close', 'volume']
        
        self.set_parameter('min_candles', min_candles)
        self.set_parameter('required_columns', self.required_columns)
    
    def process(self, data: MarketData) -> MarketData:
        """
        Validate market data.
        
        Args:
            data: Input market data
            
        Returns:
            Validated market data
            
        Raises:
            ValueError: If data validation fails
        """
        try:
            # Log validation start
            debug_helper.log_step(
                f"Data validation for {data.symbol}",
                {
                    'candles_count': len(data.candles),
                    'timeframe': data.timeframe,
                    'exchange': data.exchange
                }
            )
            
            # Check if candles DataFrame is empty
            if data.candles.empty:
                raise ValueError(f"No candles provided for {data.symbol}")
            
            # Check minimum number of candles
            if len(data.candles) < self.min_candles:
                raise ValueError(
                    f"Insufficient candles for {data.symbol}: "
                    f"got {len(data.candles)}, need at least {self.min_candles}"
                )
            
            # Check required columns
            missing_columns = [col for col in self.required_columns if col not in data.candles.columns]
            if missing_columns:
                raise ValueError(
                    f"Missing required columns for {data.symbol}: {missing_columns}"
                )
            
            # Validate data types
            self._validate_data_types(data.candles)
            
            # Validate price data
            self._validate_price_data(data.candles)
            
            # Validate volume data
            self._validate_volume_data(data.candles)
            
            # Check for NaN values
            self._validate_no_nan_values(data.candles)
            
            # Log successful validation
            debug_helper.log_step(
                f"Data validation successful for {data.symbol}",
                {
                    'candles_count': len(data.candles),
                    'columns': list(data.candles.columns),
                    'date_range': f"{data.candles.index[0]} to {data.candles.index[-1]}"
                }
            )
            
            return data
            
        except Exception as e:
            error_msg = f"Data validation failed for {data.symbol}: {str(e)}"
            debug_helper.log_step(f"Data validation error for {data.symbol}", error=e)
            raise ValueError(error_msg)
    
    def get_name(self) -> str:
        """Get step name"""
        return "DataValidation"
    
    def _validate_data_types(self, candles: pd.DataFrame) -> None:
        """
        Validate data types of candle data.
        
        Args:
            candles: DataFrame with candle data
            
        Raises:
            ValueError: If data types are invalid
        """
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        
        for col in numeric_columns:
            if col in candles.columns:
                if not pd.api.types.is_numeric_dtype(candles[col]):
                    raise ValueError(f"Column {col} must be numeric")
    
    def _validate_price_data(self, candles: pd.DataFrame) -> None:
        """
        Validate price data (OHLC).
        
        Args:
            candles: DataFrame with candle data
            
        Raises:
            ValueError: If price data is invalid
        """
        price_columns = ['open', 'high', 'low', 'close']
        
        for col in price_columns:
            if col in candles.columns:
                # Check for negative prices
                if (candles[col] <= 0).any():
                    raise ValueError(f"Column {col} contains non-positive values")
        
        # Check OHLC relationships
        if all(col in candles.columns for col in price_columns):
            # High should be >= max(open, close)
            high_check = candles['high'] >= candles[['open', 'close']].max(axis=1)
            if not high_check.all():
                raise ValueError("High price is not >= max(open, close)")
            
            # Low should be <= min(open, close)
            low_check = candles['low'] <= candles[['open', 'close']].min(axis=1)
            if not low_check.all():
                raise ValueError("Low price is not <= min(open, close)")
    
    def _validate_volume_data(self, candles: pd.DataFrame) -> None:
        """
        Validate volume data.
        
        Args:
            candles: DataFrame with candle data
            
        Raises:
            ValueError: If volume data is invalid
        """
        if 'volume' in candles.columns:
            # Check for negative volume
            if (candles['volume'] < 0).any():
                raise ValueError("Volume contains negative values")
    
    def _validate_no_nan_values(self, candles: pd.DataFrame) -> None:
        """
        Check for NaN values in critical columns.
        
        Args:
            candles: DataFrame with candle data
            
        Raises:
            ValueError: If NaN values are found
        """
        critical_columns = ['open', 'high', 'low', 'close']
        
        for col in critical_columns:
            if col in candles.columns:
                if candles[col].isna().any():
                    raise ValueError(f"Column {col} contains NaN values")
    
    def set_min_candles(self, min_candles: int) -> None:
        """
        Set minimum number of candles required.
        
        Args:
            min_candles: Minimum number of candles
        """
        self.min_candles = min_candles
        self.set_parameter('min_candles', min_candles)
    
    def set_required_columns(self, required_columns: list) -> None:
        """
        Set required columns.
        
        Args:
            required_columns: List of required column names
        """
        self.required_columns = required_columns
        self.set_parameter('required_columns', required_columns)
