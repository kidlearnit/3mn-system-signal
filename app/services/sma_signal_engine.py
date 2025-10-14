#!/usr/bin/env python3
"""
SMA Signal Engine - Logic Local/Confirmed Bullish/Bearish
"""

import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
import pandas as pd

logger = logging.getLogger(__name__)

class SMASignalType(Enum):
    """SMA Signal Types"""
    LOCAL_BULLISH_BROKEN = "local_bullish_broken"
    LOCAL_BULLISH = "local_bullish"
    CONFIRMED_BULLISH = "confirmed_bullish"
    LOCAL_BEARISH_BROKEN = "local_bearish_broken"
    LOCAL_BEARISH = "local_bearish"
    CONFIRMED_BEARISH = "confirmed_bearish"
    TRIPLE_BULLISH = "triple_bullish"
    TRIPLE_BEARISH = "triple_bearish"
    NEUTRAL = "neutral"

class SMASignalEngine:
    """Engine để tạo SMA signals theo logic Local/Confirmed"""
    
    def __init__(self):
        # Timeframe hierarchy (từ nhỏ đến lớn)
        self.timeframe_hierarchy = [
            '1m',       # 1 minute
            '2m',       # 2 minutes
            '5m',       # 5 minutes
            '15m',      # 15 minutes
            '30m',      # 30 minutes
            '1h',       # 1 hour
            '4h'        # 4 hours
        ]
        
        # Timeframe mapping cho higher TF
        self.higher_timeframe_map = {
            '1m': '2m',
            '2m': '5m',
            '5m': '15m',
            '15m': '30m',
            '30m': '1h',
            '1h': '4h',
            '4h': None  # Highest timeframe
        }
    
    def check_local_bullish_broken(self, ma_structure: Dict[str, float]) -> bool:
        """
        Kiểm tra Local Bullish Broken
        Điều kiện: CP > M1 > M2 > M3
        
        Args:
            ma_structure: MA structure dict
            
        Returns:
            True nếu Local Bullish Broken
        """
        try:
            required_fields = ['cp', 'm1', 'm2', 'm3']
            if not all(field in ma_structure for field in required_fields):
                return False
            
            cp = ma_structure['cp']
            m1 = ma_structure['m1']
            m2 = ma_structure['m2']
            m3 = ma_structure['m3']
            
            # Local Bullish Broken: CP > M1 > M2 > M3
            return cp > m1 > m2 > m3
            
        except Exception as e:
            logger.error(f"Error checking local bullish broken: {e}")
            return False
    
    def check_local_bearish_broken(self, ma_structure: Dict[str, float]) -> bool:
        """
        Kiểm tra Local Bearish Broken
        Điều kiện: CP < M1 < M2 < M3
        
        Args:
            ma_structure: MA structure dict
            
        Returns:
            True nếu Local Bearish Broken
        """
        try:
            required_fields = ['cp', 'm1', 'm2', 'm3']
            if not all(field in ma_structure for field in required_fields):
                return False
            
            cp = ma_structure['cp']
            m1 = ma_structure['m1']
            m2 = ma_structure['m2']
            m3 = ma_structure['m3']
            
            # Local Bearish Broken: CP < M1 < M2 < M3
            return cp < m1 < m2 < m3
            
        except Exception as e:
            logger.error(f"Error checking local bearish broken: {e}")
            return False
    
    def check_local_bullish(self, ma_structure: Dict[str, float]) -> bool:
        """
        Kiểm tra Local Bullish
        Điều kiện: Local Bullish Broken = True AND (M1+M2+M3)/3 > MA144
        
        Args:
            ma_structure: MA structure dict
            
        Returns:
            True nếu Local Bullish
        """
        try:
            # Phải có Local Bullish Broken trước
            if not self.check_local_bullish_broken(ma_structure):
                return False
            
            required_fields = ['avg_m1_m2_m3', 'ma144']
            if not all(field in ma_structure for field in required_fields):
                return False
            
            avg_m1_m2_m3 = ma_structure['avg_m1_m2_m3']
            ma144 = ma_structure['ma144']
            
            # Local Bullish: (M1+M2+M3)/3 > MA144
            return avg_m1_m2_m3 > ma144
            
        except Exception as e:
            logger.error(f"Error checking local bullish: {e}")
            return False
    
    def check_local_bearish(self, ma_structure: Dict[str, float]) -> bool:
        """
        Kiểm tra Local Bearish
        Điều kiện: Local Bearish Broken = True AND (M1+M2+M3)/3 < MA144
        
        Args:
            ma_structure: MA structure dict
            
        Returns:
            True nếu Local Bearish
        """
        try:
            # Phải có Local Bearish Broken trước
            if not self.check_local_bearish_broken(ma_structure):
                return False
            
            required_fields = ['avg_m1_m2_m3', 'ma144']
            if not all(field in ma_structure for field in required_fields):
                return False
            
            avg_m1_m2_m3 = ma_structure['avg_m1_m2_m3']
            ma144 = ma_structure['ma144']
            
            # Local Bearish: (M1+M2+M3)/3 < MA144
            return avg_m1_m2_m3 < ma144
            
        except Exception as e:
            logger.error(f"Error checking local bearish: {e}")
            return False
    
    def check_confirmed_bullish(self, current_tf_ma: Dict[str, float], 
                               higher_tf_ma: Dict[str, float]) -> bool:
        """
        Kiểm tra Confirmed Bullish
        Điều kiện mới: 
        A. If 1D1 local bullish = Yes; then 1D2 Local Bullish = Yes; then 1D1 is confirmed bullish.
        B. If 1D2 local bullish = Yes; then 1D5 Local Bullish = No, 1D5 is Neutral or Bearish; then 1D2 is NOT confirmed Bullish.
        C. If 1D1 and 1D2 and 1D5; all 3 are confirmed bullish then this is called TRIPLE SHORT BULLISH.
        
        Args:
            current_tf_ma: MA structure của timeframe hiện tại
            higher_tf_ma: MA structure của timeframe cao hơn
            
        Returns:
            True nếu Confirmed Bullish
        """
        try:
            # Current TF phải Local Bullish
            if not self.check_local_bullish(current_tf_ma):
                return False
            
            # Higher TF cũng phải Local Bullish (theo logic mới)
            if not self.check_local_bullish(higher_tf_ma):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking confirmed bullish: {e}")
            return False
    
    def check_confirmed_bearish(self, current_tf_ma: Dict[str, float], 
                               higher_tf_ma: Dict[str, float]) -> bool:
        """
        Kiểm tra Confirmed Bearish
        Điều kiện: Current TF Local Bearish = True AND Higher TF Local Bearish = True
        
        Args:
            current_tf_ma: MA structure của timeframe hiện tại
            higher_tf_ma: MA structure của timeframe cao hơn
            
        Returns:
            True nếu Confirmed Bearish
        """
        try:
            # Current TF phải Local Bearish
            if not self.check_local_bearish(current_tf_ma):
                return False
            
            # Higher TF cũng phải Local Bearish
            if not self.check_local_bearish(higher_tf_ma):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking confirmed bearish: {e}")
            return False
    
    def evaluate_single_timeframe(self, ma_structure: Dict[str, float]) -> SMASignalType:
        """
        Đánh giá signal cho một timeframe
        
        Args:
            ma_structure: MA structure dict
            
        Returns:
            SMASignalType
        """
        try:
            # Kiểm tra Local Bullish
            if self.check_local_bullish(ma_structure):
                return SMASignalType.LOCAL_BULLISH
            elif self.check_local_bullish_broken(ma_structure):
                return SMASignalType.LOCAL_BULLISH_BROKEN
            
            # Kiểm tra Local Bearish
            elif self.check_local_bearish(ma_structure):
                return SMASignalType.LOCAL_BEARISH
            elif self.check_local_bearish_broken(ma_structure):
                return SMASignalType.LOCAL_BEARISH_BROKEN
            
            # Neutral
            else:
                return SMASignalType.NEUTRAL
                
        except Exception as e:
            logger.error(f"Error evaluating single timeframe: {e}")
            return SMASignalType.NEUTRAL
    
    def evaluate_multi_timeframe(self, ma_structures: Dict[str, Dict[str, float]]) -> Dict[str, SMASignalType]:
        """
        Đánh giá signals cho nhiều timeframes
        
        Args:
            ma_structures: Dict {timeframe: ma_structure}
            
        Returns:
            Dict {timeframe: SMASignalType}
        """
        try:
            results = {}
            
            for timeframe, ma_structure in ma_structures.items():
                # Đánh giá single timeframe
                single_signal = self.evaluate_single_timeframe(ma_structure)
                results[timeframe] = single_signal
                
                # Kiểm tra Confirmed signals
                higher_tf = self.higher_timeframe_map.get(timeframe)
                if higher_tf and higher_tf in ma_structures:
                    higher_ma = ma_structures[higher_tf]
                    
                    # Confirmed Bullish
                    if self.check_confirmed_bullish(ma_structure, higher_ma):
                        results[timeframe] = SMASignalType.CONFIRMED_BULLISH
                    
                    # Confirmed Bearish
                    elif self.check_confirmed_bearish(ma_structure, higher_ma):
                        results[timeframe] = SMASignalType.CONFIRMED_BEARISH
            
            return results
            
        except Exception as e:
            logger.error(f"Error evaluating multi-timeframe: {e}")
            return {}
    
    def check_triple_bullish(self, ma_structures: Dict[str, Dict[str, float]]) -> bool:
        """
        Kiểm tra Triple Bullish
        Điều kiện: 1D1, 1D2, 1D5 đều Confirmed Bullish
        
        Args:
            ma_structures: Dict {timeframe: ma_structure}
            
        Returns:
            True nếu Triple Bullish
        """
        try:
            required_tfs = ['1m', '2m', '5m']
            
            for tf in required_tfs:
                if tf not in ma_structures:
                    return False
                
                # Kiểm tra Confirmed Bullish
                higher_tf = self.higher_timeframe_map.get(tf)
                if not higher_tf or higher_tf not in ma_structures:
                    return False
                
                if not self.check_confirmed_bullish(ma_structures[tf], ma_structures[higher_tf]):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking triple bullish: {e}")
            return False
    
    def check_triple_bearish(self, ma_structures: Dict[str, Dict[str, float]]) -> bool:
        """
        Kiểm tra Triple Bearish
        Điều kiện: 1D1, 1D2, 1D5 đều Confirmed Bearish
        
        Args:
            ma_structures: Dict {timeframe: ma_structure}
            
        Returns:
            True nếu Triple Bearish
        """
        try:
            required_tfs = ['1m', '2m', '5m']
            
            for tf in required_tfs:
                if tf not in ma_structures:
                    return False
                
                # Kiểm tra Confirmed Bearish
                higher_tf = self.higher_timeframe_map.get(tf)
                if not higher_tf or higher_tf not in ma_structures:
                    return False
                
                if not self.check_confirmed_bearish(ma_structures[tf], ma_structures[higher_tf]):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking triple bearish: {e}")
            return False
    
    def get_signal_strength(self, signal_type: SMASignalType) -> float:
        """
        Lấy độ mạnh của signal (0-1)
        
        Args:
            signal_type: Loại signal
            
        Returns:
            Strength score (0-1)
        """
        strength_map = {
            SMASignalType.LOCAL_BULLISH_BROKEN: 0.2,
            SMASignalType.LOCAL_BEARISH_BROKEN: 0.2,
            SMASignalType.LOCAL_BULLISH: 0.4,
            SMASignalType.LOCAL_BEARISH: 0.4,
            SMASignalType.CONFIRMED_BULLISH: 0.7,
            SMASignalType.CONFIRMED_BEARISH: 0.7,
            SMASignalType.TRIPLE_BULLISH: 1.0,
            SMASignalType.TRIPLE_BEARISH: 1.0,
            SMASignalType.NEUTRAL: 0.0
        }
        
        return strength_map.get(signal_type, 0.0)
    
    def get_signal_direction(self, signal_type: SMASignalType) -> str:
        """
        Lấy hướng của signal
        
        Args:
            signal_type: Loại signal
            
        Returns:
            'BUY', 'SELL', hoặc 'HOLD'
        """
        bullish_signals = {
            SMASignalType.LOCAL_BULLISH_BROKEN,
            SMASignalType.LOCAL_BULLISH,
            SMASignalType.CONFIRMED_BULLISH,
            SMASignalType.TRIPLE_BULLISH
        }
        
        bearish_signals = {
            SMASignalType.LOCAL_BEARISH_BROKEN,
            SMASignalType.LOCAL_BEARISH,
            SMASignalType.CONFIRMED_BEARISH,
            SMASignalType.TRIPLE_BEARISH
        }
        
        if signal_type in bullish_signals:
            return 'BUY'
        elif signal_type in bearish_signals:
            return 'SELL'
        else:
            return 'HOLD'
    
    def check_triple_bullish(self, short_tfs: List[Dict[str, float]]) -> bool:
        """
        Kiểm tra Triple Bullish
        Điều kiện: 1D1, 1D2, 1D5 tất cả đều Local Bullish
        
        Args:
            short_tfs: List of MA structures cho 1m, 2m, 5m
            
        Returns:
            True nếu Triple Bullish
        """
        try:
            if len(short_tfs) < 3:
                return False
            
            # Tất cả 3 timeframes phải Local Bullish
            for tf_ma in short_tfs:
                if not self.check_local_bullish(tf_ma):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking triple bullish: {e}")
            return False
    
    def check_triple_bearish(self, short_tfs: List[Dict[str, float]]) -> bool:
        """
        Kiểm tra Triple Bearish
        Điều kiện: 1D1, 1D2, 1D5 tất cả đều Local Bearish
        
        Args:
            short_tfs: List of MA structures cho 1m, 2m, 5m
            
        Returns:
            True nếu Triple Bearish
        """
        try:
            if len(short_tfs) < 3:
                return False
            
            # Tất cả 3 timeframes phải Local Bearish
            for tf_ma in short_tfs:
                if not self.check_local_bearish(tf_ma):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking triple bearish: {e}")
            return False

# Global instance
sma_signal_engine = SMASignalEngine()
