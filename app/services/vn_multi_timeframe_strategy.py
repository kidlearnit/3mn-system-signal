"""
VN Multi-Timeframe Strategy Implementation
Kết hợp MACD và MA across 7 timeframes cho thị trường VN
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from app.services.strategy_base import BaseStrategy, StrategyConfig, SignalResult, SignalDirection
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Get database connection"""
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "mysql"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "trader"),
        password=os.getenv("MYSQL_PASSWORD", "traderpass"),
        database=os.getenv("MYSQL_DATABASE", "trading_signals"),
        charset='utf8mb4'
    )

logger = logging.getLogger(__name__)

class VNMultiTimeframeMACDStrategy(BaseStrategy):
    """MACD Strategy cho 7 timeframes VN market"""
    
    def __init__(self):
        config = StrategyConfig(
            name="VN MACD 7 Timeframes",
            description="MACD strategy across 7 timeframes for VN market",
            version="1.0.0"
        )
        super().__init__(config)
        
    def evaluate_signal(self, symbol_id: int, ticker: str, exchange: str, timeframe: str) -> SignalResult:
        """Đánh giá MACD signal cho timeframe cụ thể"""
        try:
            # Lấy dữ liệu MACD
            macd_data = self._get_macd_data(symbol_id, timeframe)
            if not macd_data:
            return SignalResult(
                strategy_name=self.config.name,
                signal_type="MACD",
                direction=SignalDirection.NEUTRAL,
                strength=0.0,
                confidence=0.0,
                details={"error": "No MACD data available"},
                timestamp=datetime.now().isoformat(),
                timeframe=timeframe,
                symbol_id=symbol_id,
                ticker=ticker,
                exchange=exchange
            )
            
            # Phân tích MACD signal
            signal = self._analyze_macd_signal(macd_data)
            
            return SignalResult(
                direction=signal["direction"],
                strength=signal["strength"],
                confidence=signal["confidence"],
                details=signal["details"]
            )
            
        except Exception as e:
            logger.error(f"Error evaluating VN MACD strategy: {e}")
            return SignalResult(
                direction=SignalDirection.NEUTRAL,
                strength=0.0,
                confidence=0.0,
                details={"error": str(e)}
            )
    
    def _get_macd_data(self, symbol_id: int, timeframe: str) -> Optional[Dict]:
        """Lấy dữ liệu MACD từ database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Lấy 50 candles gần nhất để tính MACD
            query = """
            SELECT timestamp, macd, macd_signal, macd_histogram
            FROM indicators_macd 
            WHERE symbol_id = %s AND timeframe = %s
            ORDER BY timestamp DESC 
            LIMIT 50
            """
            
            cursor.execute(query, (symbol_id, timeframe))
            results = cursor.fetchall()
            
            if not results:
                return None
                
            # Chuyển đổi thành dict
            data = {
                "timestamps": [row[0] for row in results],
                "macd": [row[1] for row in results],
                "signal": [row[2] for row in results],
                "histogram": [row[3] for row in results]
            }
            
            cursor.close()
            conn.close()
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting MACD data: {e}")
            return None
    
    def _analyze_macd_signal(self, data: Dict) -> Dict:
        """Phân tích MACD signal"""
        try:
            macd = data["macd"]
            signal = data["signal"]
            histogram = data["histogram"]
            
            if len(macd) < 3:
                return {
                    "direction": SignalDirection.NEUTRAL,
                    "strength": 0.0,
                    "confidence": 0.0,
                    "details": {"error": "Insufficient data"}
                }
            
            # Lấy giá trị hiện tại và trước đó
            current_macd = macd[0]
            current_signal = signal[0]
            current_histogram = histogram[0]
            
            prev_macd = macd[1]
            prev_signal = signal[1]
            prev_histogram = histogram[1]
            
            # Phân tích tín hiệu
            direction = SignalDirection.NEUTRAL
            strength = 0.0
            confidence = 0.0
            details = {}
            
            # MACD crossover
            if current_macd > current_signal and prev_macd <= prev_signal:
                direction = SignalDirection.BUY
                strength = min(abs(current_histogram) * 10, 1.0)
                confidence = 0.7
                details["signal_type"] = "MACD Bullish Crossover"
                
            elif current_macd < current_signal and prev_macd >= prev_signal:
                direction = SignalDirection.SELL
                strength = min(abs(current_histogram) * 10, 1.0)
                confidence = 0.7
                details["signal_type"] = "MACD Bearish Crossover"
            
            # Histogram momentum
            elif current_histogram > prev_histogram and current_histogram > 0:
                direction = SignalDirection.BUY
                strength = min(abs(current_histogram) * 5, 0.8)
                confidence = 0.5
                details["signal_type"] = "MACD Bullish Momentum"
                
            elif current_histogram < prev_histogram and current_histogram < 0:
                direction = SignalDirection.SELL
                strength = min(abs(current_histogram) * 5, 0.8)
                confidence = 0.5
                details["signal_type"] = "MACD Bearish Momentum"
            
            # MACD divergence
            if abs(current_macd) > abs(prev_macd) * 1.2:
                if current_macd > 0:
                    direction = SignalDirection.BUY
                    strength = 0.6
                    confidence = 0.6
                    details["signal_type"] = "MACD Strong Bullish"
                else:
                    direction = SignalDirection.SELL
                    strength = 0.6
                    confidence = 0.6
                    details["signal_type"] = "MACD Strong Bearish"
            
            details.update({
                "current_macd": current_macd,
                "current_signal": current_signal,
                "current_histogram": current_histogram,
                "macd_change": current_macd - prev_macd,
                "histogram_change": current_histogram - prev_histogram
            })
            
            return {
                "direction": direction,
                "strength": strength,
                "confidence": confidence,
                "details": details
            }
            
        except Exception as e:
            logger.error(f"Error analyzing MACD signal: {e}")
            return {
                "direction": SignalDirection.NEUTRAL,
                "strength": 0.0,
                "confidence": 0.0,
                "details": {"error": str(e)}
            }


class VNMultiTimeframeMAStrategy(BaseStrategy):
    """MA Strategy cho 7 timeframes VN market"""
    
    def __init__(self):
        super().__init__()
        self.name = "VN MA 7 Timeframes"
        self.description = "Moving Average strategy across 7 timeframes for VN market"
        self.version = "1.0.0"
        self.supported_timeframes = ["1m", "2m", "5m", "15m", "30m", "1h", "4h"]
        self.required_indicators = ["sma_18", "sma_36", "sma_48", "sma_144"]
        
    def evaluate(self, symbol_id: int, timeframe: str, config: StrategyConfig) -> SignalResult:
        """Đánh giá MA signal cho timeframe cụ thể"""
        try:
            # Lấy dữ liệu MA
            ma_data = self._get_ma_data(symbol_id, timeframe)
            if not ma_data:
                return SignalResult(
                    direction=SignalDirection.NEUTRAL,
                    strength=0.0,
                    confidence=0.0,
                    details={"error": "No MA data available"}
                )
            
            # Phân tích MA signal
            signal = self._analyze_ma_signal(ma_data)
            
            return SignalResult(
                direction=signal["direction"],
                strength=signal["strength"],
                confidence=signal["confidence"],
                details=signal["details"]
            )
            
        except Exception as e:
            logger.error(f"Error evaluating VN MA strategy: {e}")
            return SignalResult(
                direction=SignalDirection.NEUTRAL,
                strength=0.0,
                confidence=0.0,
                details={"error": str(e)}
            )
    
    def _get_ma_data(self, symbol_id: int, timeframe: str) -> Optional[Dict]:
        """Lấy dữ liệu MA từ database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Lấy 50 candles gần nhất với MA values
            query = """
            SELECT timestamp, sma_18, sma_36, sma_48, sma_144, close
            FROM indicators_sma 
            WHERE symbol_id = %s AND timeframe = %s
            ORDER BY timestamp DESC 
            LIMIT 50
            """
            
            cursor.execute(query, (symbol_id, timeframe))
            results = cursor.fetchall()
            
            if not results:
                return None
                
            # Chuyển đổi thành dict
            data = {
                "timestamps": [row[0] for row in results],
                "sma_18": [row[1] for row in results],
                "sma_36": [row[2] for row in results],
                "sma_48": [row[3] for row in results],
                "sma_144": [row[4] for row in results],
                "close": [row[5] for row in results]
            }
            
            cursor.close()
            conn.close()
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting MA data: {e}")
            return None
    
    def _analyze_ma_signal(self, data: Dict) -> Dict:
        """Phân tích MA signal"""
        try:
            sma_18 = data["sma_18"]
            sma_36 = data["sma_36"]
            sma_48 = data["sma_48"]
            sma_144 = data["sma_144"]
            close = data["close"]
            
            if len(sma_18) < 3:
                return {
                    "direction": SignalDirection.NEUTRAL,
                    "strength": 0.0,
                    "confidence": 0.0,
                    "details": {"error": "Insufficient data"}
                }
            
            # Lấy giá trị hiện tại
            current_close = close[0]
            current_sma_18 = sma_18[0]
            current_sma_36 = sma_36[0]
            current_sma_48 = sma_48[0]
            current_sma_144 = sma_144[0]
            
            # Lấy giá trị trước đó
            prev_close = close[1]
            prev_sma_18 = sma_18[1]
            prev_sma_36 = sma_36[1]
            prev_sma_48 = sma_48[1]
            prev_sma_144 = sma_144[1]
            
            direction = SignalDirection.NEUTRAL
            strength = 0.0
            confidence = 0.0
            details = {}
            
            # Triple Confirmation Logic
            bullish_signals = 0
            bearish_signals = 0
            
            # 1. Price vs MA144 (trend filter)
            if current_close > current_sma_144:
                bullish_signals += 1
            else:
                bearish_signals += 1
            
            # 2. MA18 vs MA36 (short-term momentum)
            if current_sma_18 > current_sma_36:
                bullish_signals += 1
            else:
                bearish_signals += 1
            
            # 3. MA36 vs MA48 (medium-term momentum)
            if current_sma_36 > current_sma_48:
                bullish_signals += 1
            else:
                bearish_signals += 1
            
            # 4. Price momentum
            if current_close > prev_close:
                bullish_signals += 1
            else:
                bearish_signals += 1
            
            # 5. MA18 momentum
            if current_sma_18 > prev_sma_18:
                bullish_signals += 1
            else:
                bearish_signals += 1
            
            # Đánh giá tín hiệu
            total_signals = 5
            bullish_ratio = bullish_signals / total_signals
            bearish_ratio = bearish_signals / total_signals
            
            if bullish_ratio >= 0.8:  # 4/5 hoặc 5/5 signals bullish
                direction = SignalDirection.BUY
                strength = bullish_ratio
                confidence = 0.8
                details["signal_type"] = "MA Strong Bullish"
                
            elif bearish_ratio >= 0.8:  # 4/5 hoặc 5/5 signals bearish
                direction = SignalDirection.SELL
                strength = bearish_ratio
                confidence = 0.8
                details["signal_type"] = "MA Strong Bearish"
                
            elif bullish_ratio >= 0.6:  # 3/5 signals bullish
                direction = SignalDirection.BUY
                strength = bullish_ratio * 0.7
                confidence = 0.6
                details["signal_type"] = "MA Bullish"
                
            elif bearish_ratio >= 0.6:  # 3/5 signals bearish
                direction = SignalDirection.SELL
                strength = bearish_ratio * 0.7
                confidence = 0.6
                details["signal_type"] = "MA Bearish"
            
            # Tính toán chi tiết
            ma_spread = (current_sma_18 - current_sma_144) / current_sma_144 * 100
            price_vs_ma = (current_close - current_sma_144) / current_sma_144 * 100
            
            details.update({
                "bullish_signals": bullish_signals,
                "bearish_signals": bearish_signals,
                "bullish_ratio": bullish_ratio,
                "bearish_ratio": bearish_ratio,
                "ma_spread_pct": ma_spread,
                "price_vs_ma_pct": price_vs_ma,
                "current_close": current_close,
                "current_sma_18": current_sma_18,
                "current_sma_36": current_sma_36,
                "current_sma_48": current_sma_48,
                "current_sma_144": current_sma_144
            })
            
            return {
                "direction": direction,
                "strength": strength,
                "confidence": confidence,
                "details": details
            }
            
        except Exception as e:
            logger.error(f"Error analyzing MA signal: {e}")
            return {
                "direction": SignalDirection.NEUTRAL,
                "strength": 0.0,
                "confidence": 0.0,
                "details": {"error": str(e)}
            }


class VNMultiTimeframeEngine:
    """Engine để kết hợp MACD và MA across 7 timeframes"""
    
    def __init__(self):
        self.macd_strategy = VNMultiTimeframeMACDStrategy()
        self.ma_strategy = VNMultiTimeframeMAStrategy()
        self.timeframes = ["1m", "2m", "5m", "15m", "30m", "1h", "4h"]
        
    def evaluate_multi_timeframe(self, symbol_id: int) -> Dict:
        """Đánh giá tín hiệu across 7 timeframes"""
        try:
            results = {}
            
            # Đánh giá từng timeframe
            for tf in self.timeframes:
                # MACD signal
                macd_result = self.macd_strategy.evaluate(symbol_id, tf, StrategyConfig())
                
                # MA signal  
                ma_result = self.ma_strategy.evaluate(symbol_id, tf, StrategyConfig())
                
                results[tf] = {
                    "macd": {
                        "direction": macd_result.direction.value,
                        "strength": macd_result.strength,
                        "confidence": macd_result.confidence,
                        "details": macd_result.details
                    },
                    "ma": {
                        "direction": ma_result.direction.value,
                        "strength": ma_result.strength,
                        "confidence": ma_result.confidence,
                        "details": ma_result.details
                    }
                }
            
            # Tổng hợp tín hiệu
            aggregated_signal = self._aggregate_signals(results)
            
            return {
                "timeframe_results": results,
                "aggregated_signal": aggregated_signal,
                "evaluation_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in multi-timeframe evaluation: {e}")
            return {
                "error": str(e),
                "evaluation_time": datetime.now().isoformat()
            }
    
    def _aggregate_signals(self, results: Dict) -> Dict:
        """Tổng hợp tín hiệu từ 7 timeframes"""
        try:
            # Tính trọng số cho từng timeframe
            timeframe_weights = {
                "1m": 0.1,   # 10%
                "2m": 0.1,   # 10%
                "5m": 0.15,  # 15%
                "15m": 0.15, # 15%
                "30m": 0.2,  # 20%
                "1h": 0.15,  # 15%
                "4h": 0.15   # 15%
            }
            
            # Tổng hợp MACD signals
            macd_buy_weight = 0.0
            macd_sell_weight = 0.0
            macd_total_confidence = 0.0
            
            # Tổng hợp MA signals
            ma_buy_weight = 0.0
            ma_sell_weight = 0.0
            ma_total_confidence = 0.0
            
            for tf, weight in timeframe_weights.items():
                if tf in results:
                    # MACD aggregation
                    macd = results[tf]["macd"]
                    if macd["direction"] == "BUY":
                        macd_buy_weight += weight * macd["strength"] * macd["confidence"]
                    elif macd["direction"] == "SELL":
                        macd_sell_weight += weight * macd["strength"] * macd["confidence"]
                    macd_total_confidence += weight * macd["confidence"]
                    
                    # MA aggregation
                    ma = results[tf]["ma"]
                    if ma["direction"] == "BUY":
                        ma_buy_weight += weight * ma["strength"] * ma["confidence"]
                    elif ma["direction"] == "SELL":
                        ma_sell_weight += weight * ma["strength"] * ma["confidence"]
                    ma_total_confidence += weight * ma["confidence"]
            
            # Kết hợp MACD và MA
            total_buy_weight = (macd_buy_weight + ma_buy_weight) / 2
            total_sell_weight = (macd_sell_weight + ma_sell_weight) / 2
            total_confidence = (macd_total_confidence + ma_total_confidence) / 2
            
            # Xác định direction cuối cùng
            if total_buy_weight > total_sell_weight and total_buy_weight > 0.3:
                final_direction = "BUY"
                final_strength = min(total_buy_weight, 1.0)
            elif total_sell_weight > total_buy_weight and total_sell_weight > 0.3:
                final_direction = "SELL"
                final_strength = min(total_sell_weight, 1.0)
            else:
                final_direction = "NEUTRAL"
                final_strength = 0.0
            
            return {
                "direction": final_direction,
                "strength": final_strength,
                "confidence": min(total_confidence, 1.0),
                "macd_buy_weight": macd_buy_weight,
                "macd_sell_weight": macd_sell_weight,
                "ma_buy_weight": ma_buy_weight,
                "ma_sell_weight": ma_sell_weight,
                "total_buy_weight": total_buy_weight,
                "total_sell_weight": total_sell_weight,
                "timeframe_breakdown": {
                    tf: {
                        "macd_direction": results[tf]["macd"]["direction"],
                        "ma_direction": results[tf]["ma"]["direction"],
                        "weight": timeframe_weights[tf]
                    } for tf in self.timeframes if tf in results
                }
            }
            
        except Exception as e:
            logger.error(f"Error aggregating signals: {e}")
            return {
                "direction": "NEUTRAL",
                "strength": 0.0,
                "confidence": 0.0,
                "error": str(e)
            }
