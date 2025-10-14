#!/usr/bin/env python3
"""
SMA Indicators Service - Tính toán Simple Moving Averages
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class SMAIndicatorService:
    """Service để tính toán các SMA indicators"""
    
    def __init__(self):
        # SMA periods theo hệ thống
        self.sma_periods = {
            'm1': 18,    # MA18 - Short term
            'm2': 36,    # MA36 - Medium term  
            'm3': 48,    # MA48 - Long term
            'ma144': 144 # MA144 - Resistance level
        }
        
        # Timeframe mapping
        self.timeframe_mapping = {
            '1D4hr': '4h',
            '1D1hr': '1h', 
            '1D30Min': '30m',
            '1D15Min': '15m',
            '1D5': '5m',      # 1D5 = 5m
            '1D2': '2m',      # 1D2 = 2m  
            '1D1': '1m'       # 1D1 = 1m
        }
    
    def calculate_sma(self, data: pd.Series, period: int) -> pd.Series:
        """
        Tính Simple Moving Average
        
        Args:
            data: Series giá close
            period: Số period cho SMA
            
        Returns:
            Series SMA values
        """
        try:
            return data.rolling(window=period, min_periods=1).mean()
        except Exception as e:
            logger.error(f"Error calculating SMA({period}): {e}")
            return pd.Series(dtype=float)
    
    def calculate_all_smas(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Tính tất cả SMA indicators
        
        Args:
            data: DataFrame với columns ['close', 'high', 'low', 'volume', 'timestamp']
            
        Returns:
            Dict chứa tất cả SMA values
        """
        try:
            if 'close' not in data.columns:
                raise ValueError("DataFrame must contain 'close' column")
            
            sma_results = {}
            
            # Tính từng SMA
            for name, period in self.sma_periods.items():
                sma_results[name] = self.calculate_sma(data['close'], period)
            
            # Tính average của M1, M2, M3
            if all(name in sma_results for name in ['m1', 'm2', 'm3']):
                sma_results['avg_m1_m2_m3'] = (
                    sma_results['m1'] + sma_results['m2'] + sma_results['m3']
                ) / 3
            
            return sma_results
            
        except Exception as e:
            logger.error(f"Error calculating all SMAs: {e}")
            return {}
    
    def get_ma_structure(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        Lấy MA structure cho signal evaluation
        
        Args:
            data: DataFrame với price data
            
        Returns:
            Dict chứa MA structure values
        """
        try:
            if data.empty:
                return {}
            
            # Tính tất cả SMAs
            sma_results = self.calculate_all_smas(data)
            
            if not sma_results:
                return {}
            
            # Lấy giá trị cuối cùng
            latest_idx = data.index[-1]
            
            structure = {
                'cp': float(data['close'].iloc[-1]),  # Current Price
                'm1': float(sma_results.get('m1', pd.Series()).iloc[-1]) if 'm1' in sma_results else None,
                'm2': float(sma_results.get('m2', pd.Series()).iloc[-1]) if 'm2' in sma_results else None,
                'm3': float(sma_results.get('m3', pd.Series()).iloc[-1]) if 'm3' in sma_results else None,
                'ma144': float(sma_results.get('ma144', pd.Series()).iloc[-1]) if 'ma144' in sma_results else None,
                'avg_m1_m2_m3': float(sma_results.get('avg_m1_m2_m3', pd.Series()).iloc[-1]) if 'avg_m1_m2_m3' in sma_results else None,
                'timestamp': latest_idx,
                'volume': float(data['volume'].iloc[-1]) if 'volume' in data.columns else None,
                'high': float(data['high'].iloc[-1]) if 'high' in data.columns else None,
                'low': float(data['low'].iloc[-1]) if 'low' in data.columns else None
            }
            
            # Loại bỏ None values
            structure = {k: v for k, v in structure.items() if v is not None}
            
            return structure
            
        except Exception as e:
            logger.error(f"Error getting MA structure: {e}")
            return {}
    
    def get_ma_structure_for_timeframe(self, symbol_id: int, timeframe: str) -> Dict[str, float]:
        """
        Lấy MA structure cho symbol và timeframe cụ thể
        
        Args:
            symbol_id: ID của symbol
            timeframe: Timeframe (1D4hr, 1D1hr, etc.)
            
        Returns:
            Dict chứa MA structure
        """
        try:
            from app.services.data_sources import get_candles_for_tf
            
            # Lấy data cho timeframe
            data = get_candles_for_tf(symbol_id, timeframe)
            
            if data is None or data.empty:
                logger.warning(f"No data for symbol_id={symbol_id}, timeframe={timeframe}")
                return {}
            
            # Tính MA structure
            ma_structure = self.get_ma_structure(data)
            
            # Thêm metadata
            ma_structure.update({
                'symbol_id': symbol_id,
                'timeframe': timeframe,
                'data_points': len(data)
            })
            
            return ma_structure
            
        except Exception as e:
            logger.error(f"Error getting MA structure for {symbol_id}/{timeframe}: {e}")
            return {}
    
    def validate_ma_structure(self, ma_structure: Dict[str, float]) -> bool:
        """
        Validate MA structure có đủ data không
        
        Args:
            ma_structure: MA structure dict
            
        Returns:
            True nếu valid, False nếu không
        """
        required_fields = ['cp', 'm1', 'm2', 'm3', 'ma144', 'avg_m1_m2_m3']
        
        for field in required_fields:
            if field not in ma_structure:
                logger.warning(f"Missing required field: {field}")
                return False
            
            if ma_structure[field] is None or np.isnan(ma_structure[field]):
                logger.warning(f"Invalid value for field: {field}")
                return False
        
        return True
    
    def get_ma_trend_direction(self, ma_structure: Dict[str, float]) -> str:
        """
        Xác định hướng trend từ MA structure
        
        Args:
            ma_structure: MA structure dict
            
        Returns:
            'bullish', 'bearish', hoặc 'neutral'
        """
        try:
            if not self.validate_ma_structure(ma_structure):
                return 'neutral'
            
            cp = ma_structure['cp']
            m1 = ma_structure['m1']
            m2 = ma_structure['m2']
            m3 = ma_structure['m3']
            
            # Bullish: CP > M1 > M2 > M3
            if cp > m1 > m2 > m3:
                return 'bullish'
            
            # Bearish: CP < M1 < M2 < M3
            elif cp < m1 < m2 < m3:
                return 'bearish'
            
            # Neutral: Không có pattern rõ ràng
            else:
                return 'neutral'
                
        except Exception as e:
            logger.error(f"Error determining MA trend direction: {e}")
            return 'neutral'
    
    def get_ma_strength(self, ma_structure: Dict[str, float]) -> float:
        """
        Tính độ mạnh của MA trend (0-1)
        
        Args:
            ma_structure: MA structure dict
            
        Returns:
            Strength score (0-1)
        """
        try:
            if not self.validate_ma_structure(ma_structure):
                return 0.0
            
            cp = ma_structure['cp']
            m1 = ma_structure['m1']
            m2 = ma_structure['m2']
            m3 = ma_structure['m3']
            
            # Tính khoảng cách giữa các MA
            gap1 = abs(cp - m1) / m1 if m1 != 0 else 0
            gap2 = abs(m1 - m2) / m2 if m2 != 0 else 0
            gap3 = abs(m2 - m3) / m3 if m3 != 0 else 0
            
            # Strength = average gap (normalized)
            avg_gap = (gap1 + gap2 + gap3) / 3
            strength = min(avg_gap * 10, 1.0)  # Scale to 0-1
            
            return strength
            
        except Exception as e:
            logger.error(f"Error calculating MA strength: {e}")
            return 0.0

# Global instance
sma_indicator_service = SMAIndicatorService()
