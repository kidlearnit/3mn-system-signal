#!/usr/bin/env python3
"""
Enhanced Signal Engine - Professional Trading Signals
Combines multiple indicators with risk management and data quality checks
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SignalQuality:
    """Signal quality metrics"""
    confidence: float  # 0-1
    strength: float    # 0-1
    risk_score: float  # 0-1 (higher = riskier)
    data_quality: float # 0-1
    volume_confirmation: bool
    volatility_filter: bool
    trend_alignment: bool

@dataclass
class RiskMetrics:
    """Risk management metrics"""
    atr: float  # Average True Range
    stop_loss: float
    take_profit: float
    position_size: float
    risk_reward_ratio: float
    max_drawdown: float

class EnhancedSignalType(Enum):
    """Enhanced signal types with quality levels"""
    STRONG_BUY = "strong_buy"           # High confidence, low risk
    BUY = "buy"                         # Medium confidence
    WEAK_BUY = "weak_buy"               # Low confidence, high risk
    HOLD = "hold"                       # No clear direction
    WEAK_SELL = "weak_sell"             # Low confidence, high risk
    SELL = "sell"                       # Medium confidence
    STRONG_SELL = "strong_sell"         # High confidence, low risk

class EnhancedSignalEngine:
    """Professional-grade signal engine for real trading"""
    
    def __init__(self):
        self.min_data_points = 200  # More data for better signals
        self.volume_threshold = 1.5  # 1.5x average volume
        self.volatility_threshold = 0.02  # 2% daily volatility
        
    def analyze_signal_quality(self, candles: pd.DataFrame, 
                             ma_structure: Dict[str, float],
                             volume_data: Dict[str, float]) -> SignalQuality:
        """Analyze signal quality with multiple factors"""
        
        # 1. Data Quality Check
        data_quality = self._check_data_quality(candles)
        
        # 2. Volume Confirmation
        volume_confirmation = self._check_volume_confirmation(volume_data)
        
        # 3. Volatility Filter
        volatility_filter = self._check_volatility_filter(candles)
        
        # 4. Trend Alignment
        trend_alignment = self._check_trend_alignment(ma_structure)
        
        # 5. Calculate Confidence
        confidence = self._calculate_confidence(
            data_quality, volume_confirmation, volatility_filter, trend_alignment
        )
        
        # 6. Calculate Strength
        strength = self._calculate_signal_strength(ma_structure)
        
        # 7. Calculate Risk Score
        risk_score = self._calculate_risk_score(candles, ma_structure)
        
        return SignalQuality(
            confidence=confidence,
            strength=strength,
            risk_score=risk_score,
            data_quality=data_quality,
            volume_confirmation=volume_confirmation,
            volatility_filter=volatility_filter,
            trend_alignment=trend_alignment
        )
    
    def calculate_risk_metrics(self, candles: pd.DataFrame, 
                             current_price: float) -> RiskMetrics:
        """Calculate risk management metrics"""
        
        # Convert to float to avoid Decimal issues
        current_price = float(current_price)
        
        # 1. ATR (Average True Range)
        atr = self._calculate_atr(candles)
        
        # 2. Stop Loss (2x ATR)
        stop_loss = current_price - (2 * atr)
        
        # 3. Take Profit (3x ATR for 1.5:1 risk/reward)
        take_profit = current_price + (3 * atr)
        
        # 4. Position Size (1% risk per trade)
        position_size = self._calculate_position_size(current_price, stop_loss)
        
        # 5. Risk/Reward Ratio
        risk_reward_ratio = (take_profit - current_price) / (current_price - stop_loss)
        
        # 6. Max Drawdown
        max_drawdown = self._calculate_max_drawdown(candles)
        
        return RiskMetrics(
            atr=atr,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=position_size,
            risk_reward_ratio=risk_reward_ratio,
            max_drawdown=max_drawdown
        )
    
    def generate_enhanced_signal(self, candles: pd.DataFrame,
                               ma_structure: Dict[str, float],
                               volume_data: Dict[str, float]) -> Dict[str, Any]:
        """Generate enhanced trading signal with full analysis"""
        
        # 1. Basic SMA Signal
        basic_signal = self._get_basic_sma_signal(ma_structure)
        
        # 2. Signal Quality Analysis
        quality = self.analyze_signal_quality(candles, ma_structure, volume_data)
        
        # 3. Risk Metrics
        current_price = ma_structure['cp']
        risk_metrics = self.calculate_risk_metrics(candles, current_price)
        
        # 4. Enhanced Signal Type
        enhanced_signal = self._determine_enhanced_signal(basic_signal, quality)
        
        # 5. Trading Recommendation
        recommendation = self._generate_trading_recommendation(
            enhanced_signal, quality, risk_metrics
        )
        
        return {
            'signal_type': enhanced_signal.value,
            'basic_signal': basic_signal,
            'quality': quality,
            'risk_metrics': risk_metrics,
            'recommendation': recommendation,
            'timestamp': datetime.now(),
            'confidence_score': quality.confidence,
            'risk_score': quality.risk_score
        }
    
    def _check_data_quality(self, candles: pd.DataFrame) -> float:
        """Check data quality score (0-1)"""
        try:
            # Check for missing data
            expected_intervals = len(candles) * 0.95  # Allow 5% missing
            actual_count = len(candles.dropna())
            completeness = actual_count / len(candles)
            
            # Check for data anomalies
            anomalies = 0
            for i in range(1, len(candles)):
                prev_close = candles.iloc[i-1]['close']
                curr_close = candles.iloc[i]['close']
                
                # Check for price jumps > 10%
                if prev_close > 0:
                    price_change = abs(curr_close - prev_close) / prev_close
                    if price_change > 0.1:
                        anomalies += 1
            
            anomaly_rate = anomalies / len(candles) if len(candles) > 0 else 0
            quality_score = completeness * (1 - anomaly_rate)
            
            return max(0.0, min(1.0, quality_score))
            
        except Exception as e:
            logger.error(f"Error checking data quality: {e}")
            return 0.0
    
    def _check_volume_confirmation(self, volume_data: Dict[str, float]) -> bool:
        """Check if volume confirms the signal"""
        try:
            current_volume = float(volume_data.get('current', 0))
            avg_volume = float(volume_data.get('average', 0))
            
            if avg_volume > 0:
                volume_ratio = current_volume / avg_volume
                return volume_ratio >= self.volume_threshold
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking volume confirmation: {e}")
            return False
    
    def _check_volatility_filter(self, candles: pd.DataFrame) -> bool:
        """Check if volatility is within acceptable range"""
        try:
            # Calculate daily volatility
            returns = candles['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # Annualized
            
            return volatility >= self.volatility_threshold
            
        except Exception as e:
            logger.error(f"Error checking volatility filter: {e}")
            return False
    
    def _check_trend_alignment(self, ma_structure: Dict[str, float]) -> bool:
        """Check if all timeframes are aligned"""
        try:
            cp = ma_structure['cp']
            m1 = ma_structure['m1']
            m2 = ma_structure['m2']
            m3 = ma_structure['m3']
            ma144 = ma_structure['ma144']
            
            # Check if all MAs are aligned
            bullish_alignment = cp > m1 > m2 > m3 > ma144
            bearish_alignment = cp < m1 < m2 < m3 < ma144
            
            return bullish_alignment or bearish_alignment
            
        except Exception as e:
            logger.error(f"Error checking trend alignment: {e}")
            return False
    
    def _calculate_confidence(self, data_quality: float, volume_confirmation: bool,
                            volatility_filter: bool, trend_alignment: bool) -> float:
        """Calculate overall confidence score"""
        factors = [
            data_quality,
            1.0 if volume_confirmation else 0.0,
            1.0 if volatility_filter else 0.0,
            1.0 if trend_alignment else 0.0
        ]
        
        return sum(factors) / len(factors)
    
    def _calculate_signal_strength(self, ma_structure: Dict[str, float]) -> float:
        """Calculate signal strength based on MA separation"""
        try:
            cp = float(ma_structure['cp'])
            m1 = float(ma_structure['m1'])
            m2 = float(ma_structure['m2'])
            m3 = float(ma_structure['m3'])
            
            # Calculate percentage separation
            separation = abs(cp - m3) / m3 if m3 > 0 else 0
            return min(1.0, separation * 10)  # Scale to 0-1
            
        except Exception as e:
            logger.error(f"Error calculating signal strength: {e}")
            return 0.0
    
    def _calculate_risk_score(self, candles: pd.DataFrame, 
                            ma_structure: Dict[str, float]) -> float:
        """Calculate risk score (0-1, higher = riskier)"""
        try:
            # Calculate volatility
            returns = candles['close'].pct_change().dropna()
            volatility = returns.std()
            
            # Calculate trend strength
            cp = float(ma_structure['cp'])
            m3 = float(ma_structure['m3'])
            trend_strength = abs(cp - m3) / m3 if m3 > 0 else 0
            
            # Higher volatility and lower trend strength = higher risk
            risk_score = (volatility * 2) + (1 - trend_strength)
            return max(0.0, min(1.0, risk_score))
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 1.0
    
    def _calculate_atr(self, candles: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
            high = candles['high']
            low = candles['low']
            close = candles['close']
            
            # True Range
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean().iloc[-1]
            
            return atr if not pd.isna(atr) else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return 0.0
    
    def _calculate_position_size(self, current_price: float, stop_loss: float) -> float:
        """Calculate position size based on 1% risk"""
        try:
            risk_per_trade = 0.01  # 1% risk
            risk_amount = current_price - stop_loss
            
            if risk_amount > 0:
                position_size = risk_per_trade / (risk_amount / current_price)
                return min(position_size, 1.0)  # Max 100% position
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.0
    
    def _calculate_max_drawdown(self, candles: pd.DataFrame) -> float:
        """Calculate maximum drawdown"""
        try:
            cumulative = (1 + candles['close'].pct_change()).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            return abs(drawdown.min())
            
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {e}")
            return 0.0
    
    def _get_basic_sma_signal(self, ma_structure: Dict[str, float]) -> str:
        """Get basic SMA signal"""
        try:
            cp = float(ma_structure['cp'])
            m1 = float(ma_structure['m1'])
            m2 = float(ma_structure['m2'])
            m3 = float(ma_structure['m3'])
            
            if cp > m1 > m2 > m3:
                return "bullish"
            elif cp < m1 < m2 < m3:
                return "bearish"
            else:
                return "neutral"
                
        except Exception as e:
            logger.error(f"Error getting basic SMA signal: {e}")
            return "neutral"
    
    def _determine_enhanced_signal(self, basic_signal: str, 
                                 quality: SignalQuality) -> EnhancedSignalType:
        """Determine enhanced signal type based on quality"""
        
        if basic_signal == "bullish":
            if quality.confidence >= 0.8 and quality.risk_score <= 0.3:
                return EnhancedSignalType.STRONG_BUY
            elif quality.confidence >= 0.6 and quality.risk_score <= 0.5:
                return EnhancedSignalType.BUY
            else:
                return EnhancedSignalType.WEAK_BUY
                
        elif basic_signal == "bearish":
            if quality.confidence >= 0.8 and quality.risk_score <= 0.3:
                return EnhancedSignalType.STRONG_SELL
            elif quality.confidence >= 0.6 and quality.risk_score <= 0.5:
                return EnhancedSignalType.SELL
            else:
                return EnhancedSignalType.WEAK_SELL
                
        else:
            return EnhancedSignalType.HOLD
    
    def _generate_trading_recommendation(self, signal: EnhancedSignalType,
                                       quality: SignalQuality,
                                       risk_metrics: RiskMetrics) -> Dict[str, Any]:
        """Generate trading recommendation"""
        
        recommendation = {
            'action': signal.value,
            'confidence': quality.confidence,
            'risk_level': 'LOW' if quality.risk_score <= 0.3 else 
                         'MEDIUM' if quality.risk_score <= 0.6 else 'HIGH',
            'stop_loss': risk_metrics.stop_loss,
            'take_profit': risk_metrics.take_profit,
            'position_size': risk_metrics.position_size,
            'risk_reward_ratio': risk_metrics.risk_reward_ratio,
            'max_drawdown': risk_metrics.max_drawdown,
            'notes': []
        }
        
        # Add notes based on quality factors
        if not quality.volume_confirmation:
            recommendation['notes'].append("Low volume - signal may be weak")
        
        if not quality.volatility_filter:
            recommendation['notes'].append("Low volatility - consider waiting")
        
        if not quality.trend_alignment:
            recommendation['notes'].append("Timeframes not aligned - higher risk")
        
        if quality.data_quality < 0.8:
            recommendation['notes'].append("Data quality issues detected")
        
        return recommendation

# Global instance
enhanced_signal_engine = EnhancedSignalEngine()
