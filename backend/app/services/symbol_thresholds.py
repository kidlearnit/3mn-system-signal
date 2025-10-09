"""
Service để quản lý thresholds riêng cho từng cổ phiếu và thị trường
"""

from sqlalchemy import text
from ..db import SessionLocal
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class SymbolThresholdService:
    """Service quản lý thresholds cho từng symbol"""
    
    def __init__(self):
        self.cache = {}  # Cache để tăng performance
    
    def get_symbol_thresholds(self, symbol_id: int, timeframe: str) -> List[Dict]:
        """
        Lấy thresholds cho một symbol cụ thể
        
        Args:
            symbol_id: ID của symbol
            timeframe: Timeframe (1m, 2m, 5m, 15m, 30m, 1h, 4h, 1D)
            
        Returns:
            List of threshold rules
        """
        cache_key = f"{symbol_id}_{timeframe}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            if SessionLocal is None:
                logger.error("SessionLocal not initialized")
                return []
            
            with SessionLocal() as s:
                # Lấy thresholds từ symbol_thresholds_view
                rows = s.execute(text("""
                    SELECT indicator, zone, comparison, min_value, max_value
                    FROM symbol_thresholds_view
                    WHERE symbol_id = :symbol_id 
                    AND timeframe = :timeframe
                    AND is_active = TRUE
                    ORDER BY FIELD(zone, 'igr','greed','bull','pos','neutral','neg','bear','fear','panic') DESC
                """), {'symbol_id': symbol_id, 'timeframe': timeframe}).mappings().all()
                
                thresholds = [dict(r) for r in rows]
                
                # Cache kết quả
                self.cache[cache_key] = thresholds
                
                return thresholds
                
        except Exception as e:
            logger.error(f"Error getting symbol thresholds: {e}")
            return []
    
    def get_market_thresholds(self, market_type: str, timeframe: str) -> List[Dict]:
        """
        Lấy thresholds mặc định cho một thị trường
        
        Args:
            market_type: US, VN, GLOBAL
            timeframe: Timeframe
            
        Returns:
            List of threshold rules
        """
        cache_key = f"market_{market_type}_{timeframe}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            if SessionLocal is None:
                logger.error("SessionLocal not initialized")
                return []
            
            with SessionLocal() as s:
                rows = s.execute(text("""
                    SELECT indicator, zone, comparison, min_value, max_value
                    FROM market_threshold_templates_view
                    WHERE market_type = :market_type 
                    AND timeframe = :timeframe
                    ORDER BY FIELD(zone, 'igr','greed','bull','pos','neutral','neg','bear','fear','panic') DESC
                """), {'market_type': market_type, 'timeframe': timeframe}).mappings().all()
                
                thresholds = [dict(r) for r in rows]
                
                # Cache kết quả
                self.cache[cache_key] = thresholds
                
                return thresholds
                
        except Exception as e:
            logger.error(f"Error getting market thresholds: {e}")
            return []
    
    def get_symbol_market_type(self, symbol_id: int) -> str:
        """
        Lấy market type của symbol
        
        Args:
            symbol_id: ID của symbol
            
        Returns:
            Market type (US, VN, GLOBAL)
        """
        try:
            if SessionLocal is None:
                logger.error("SessionLocal not initialized")
                return 'GLOBAL'
            
            with SessionLocal() as s:
                result = s.execute(text("""
                    SELECT market_type FROM symbols WHERE id = :symbol_id
                """), {'symbol_id': symbol_id}).scalar()
                
                return result or 'GLOBAL'
                
        except Exception as e:
            logger.error(f"Error getting symbol market type: {e}")
            return 'GLOBAL'
    
    def update_symbol_thresholds(self, symbol_id: int, timeframe: str, 
                                indicator: str, zone: str, 
                                comparison: str, min_value: float, 
                                max_value: Optional[float] = None) -> bool:
        """
        Cập nhật threshold cho một symbol cụ thể
        
        Args:
            symbol_id: ID của symbol
            timeframe: Timeframe
            indicator: fmacd, smacd, bars
            zone: igr, greed, bull, pos, neutral, neg, bear, fear, panic
            comparison: >=, <, >, <=, between
            min_value: Giá trị tối thiểu
            max_value: Giá trị tối đa (optional)
            
        Returns:
            True nếu thành công
        """
        try:
            with SessionLocal() as s:
                # Lấy symbol_threshold_id
                symbol_threshold_id = s.execute(text("""
                    SELECT id FROM symbol_thresholds 
                    WHERE symbol_id = :symbol_id AND is_active = TRUE
                """), {'symbol_id': symbol_id}).scalar()
                
                if not symbol_threshold_id:
                    logger.error(f"No active symbol threshold found for symbol_id {symbol_id}")
                    return False
                
                # Cập nhật hoặc tạo mới threshold value
                s.execute(text("""
                    INSERT INTO symbol_threshold_values 
                    (symbol_threshold_id, timeframe, indicator, zone, comparison, min_value, max_value)
                    VALUES (:symbol_threshold_id, :timeframe, :indicator, :zone, :comparison, :min_value, :max_value)
                    ON DUPLICATE KEY UPDATE 
                        comparison = VALUES(comparison),
                        min_value = VALUES(min_value),
                        max_value = VALUES(max_value)
                """), {
                    'symbol_threshold_id': symbol_threshold_id,
                    'timeframe': timeframe,
                    'indicator': indicator,
                    'zone': zone,
                    'comparison': comparison,
                    'min_value': min_value,
                    'max_value': max_value
                })
                
                s.commit()
                
                # Clear cache
                self.clear_cache_for_symbol(symbol_id)
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating symbol thresholds: {e}")
            return False
    
    def reset_symbol_to_market_defaults(self, symbol_id: int) -> bool:
        """
        Reset symbol thresholds về mặc định của thị trường
        
        Args:
            symbol_id: ID của symbol
            
        Returns:
            True nếu thành công
        """
        try:
            with SessionLocal() as s:
                # Lấy market type của symbol
                market_type = self.get_symbol_market_type(symbol_id)
                
                # Lấy symbol_threshold_id
                symbol_threshold_id = s.execute(text("""
                    SELECT id FROM symbol_thresholds 
                    WHERE symbol_id = :symbol_id AND is_active = TRUE
                """), {'symbol_id': symbol_id}).scalar()
                
                if not symbol_threshold_id:
                    logger.error(f"No active symbol threshold found for symbol_id {symbol_id}")
                    return False
                
                # Xóa tất cả threshold values hiện tại
                s.execute(text("""
                    DELETE FROM symbol_threshold_values 
                    WHERE symbol_threshold_id = :symbol_threshold_id
                """), {'symbol_threshold_id': symbol_threshold_id})
                
                # Copy từ market template
                s.execute(text("""
                    INSERT INTO symbol_threshold_values 
                    (symbol_threshold_id, timeframe, indicator, zone, comparison, min_value, max_value)
                    SELECT 
                        :symbol_threshold_id,
                        mtv.timeframe,
                        mtv.indicator,
                        mtv.zone,
                        mtv.comparison,
                        mtv.min_value,
                        mtv.max_value
                    FROM market_threshold_template_values mtv
                    JOIN market_threshold_templates mt ON mt.id = mtv.template_id
                    WHERE mt.market_type = :market_type AND mt.is_default = TRUE
                """), {
                    'symbol_threshold_id': symbol_threshold_id,
                    'market_type': market_type
                })
                
                s.commit()
                
                # Clear cache
                self.clear_cache_for_symbol(symbol_id)
                
                return True
                
        except Exception as e:
            logger.error(f"Error resetting symbol to market defaults: {e}")
            return False
    
    def clear_cache_for_symbol(self, symbol_id: int):
        """Clear cache cho một symbol"""
        keys_to_remove = [key for key in self.cache.keys() if key.startswith(f"{symbol_id}_")]
        for key in keys_to_remove:
            del self.cache[key]
    
    def clear_all_cache(self):
        """Clear toàn bộ cache"""
        self.cache.clear()
    
    def get_thresholds_summary(self) -> Dict:
        """
        Lấy tổng quan về thresholds trong hệ thống
        
        Returns:
            Dictionary với thống kê
        """
        try:
            with SessionLocal() as s:
                # Đếm symbols theo market type
                symbols_by_market = s.execute(text("""
                    SELECT market_type, COUNT(*) as count
                    FROM symbols 
                    WHERE active = 1
                    GROUP BY market_type
                """)).fetchall()
                
                # Đếm symbol thresholds
                symbol_thresholds_count = s.execute(text("""
                    SELECT COUNT(*) FROM symbol_thresholds WHERE is_active = TRUE
                """)).scalar()
                
                # Đếm symbol threshold values
                symbol_values_count = s.execute(text("""
                    SELECT COUNT(*) FROM symbol_threshold_values stv
                    JOIN symbol_thresholds st ON st.id = stv.symbol_threshold_id
                    WHERE st.is_active = TRUE
                """)).scalar()
                
                # Đếm market templates
                market_templates_count = s.execute(text("""
                    SELECT COUNT(*) FROM market_threshold_templates WHERE is_default = TRUE
                """)).scalar()
                
                return {
                    'symbols_by_market': dict(symbols_by_market),
                    'symbol_thresholds_count': symbol_thresholds_count,
                    'symbol_values_count': symbol_values_count,
                    'market_templates_count': market_templates_count
                }
                
        except Exception as e:
            logger.error(f"Error getting thresholds summary: {e}")
            return {}

# Global instance
symbol_threshold_service = SymbolThresholdService()

def get_symbol_thresholds(symbol_id: int, timeframe: str) -> List[Dict]:
    """Convenience function để lấy symbol thresholds"""
    return symbol_threshold_service.get_symbol_thresholds(symbol_id, timeframe)

def get_market_thresholds(market_type: str, timeframe: str) -> List[Dict]:
    """Convenience function để lấy market thresholds"""
    return symbol_threshold_service.get_market_thresholds(market_type, timeframe)

def get_symbol_market_type(symbol_id: int) -> str:
    """Convenience function để lấy symbol market type"""
    return symbol_threshold_service.get_symbol_market_type(symbol_id)
