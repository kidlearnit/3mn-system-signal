#!/usr/bin/env python3
"""
Portfolio Management System
Manages position sizing, risk, and portfolio optimization
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)

@dataclass
class Position:
    """Trading position"""
    symbol: str
    exchange: str
    side: str  # 'long' or 'short'
    size: float
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    entry_time: datetime
    unrealized_pnl: float
    risk_amount: float

@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics"""
    total_value: float
    total_pnl: float
    total_pnl_pct: float
    daily_pnl: float
    daily_pnl_pct: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    total_trades: int
    open_positions: int
    risk_per_trade: float
    total_risk: float

class RiskLevel(Enum):
    """Risk levels"""
    CONSERVATIVE = "conservative"  # 0.5% risk per trade
    MODERATE = "moderate"         # 1% risk per trade
    AGGRESSIVE = "aggressive"     # 2% risk per trade

class PortfolioManager:
    """Professional portfolio management system"""
    
    def __init__(self, initial_capital: float = 100000, risk_level: RiskLevel = RiskLevel.MODERATE):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_level = risk_level
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Dict] = []
        self.daily_returns: List[float] = []
        
        # Risk parameters
        self.risk_per_trade = self._get_risk_per_trade()
        self.max_positions = 10
        self.max_correlation = 0.7
        self.max_sector_exposure = 0.3
        
    def _get_risk_per_trade(self) -> float:
        """Get risk per trade based on risk level"""
        risk_map = {
            RiskLevel.CONSERVATIVE: 0.005,  # 0.5%
            RiskLevel.MODERATE: 0.01,       # 1%
            RiskLevel.AGGRESSIVE: 0.02      # 2%
        }
        return risk_map[self.risk_level]
    
    def calculate_position_size(self, symbol: str, entry_price: float, 
                              stop_loss: float, signal_confidence: float) -> float:
        """Calculate optimal position size"""
        
        # 1. Base position size from risk
        risk_amount = self.current_capital * self.risk_per_trade
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk <= 0:
            return 0.0
        
        base_size = risk_amount / price_risk
        
        # 2. Adjust for signal confidence
        confidence_multiplier = 0.5 + (signal_confidence * 0.5)  # 0.5 to 1.0
        adjusted_size = base_size * confidence_multiplier
        
        # 3. Check portfolio constraints
        max_size = self._get_max_position_size(symbol, entry_price)
        final_size = min(adjusted_size, max_size)
        
        # 4. Check available capital
        required_capital = final_size * entry_price
        if required_capital > self.current_capital * 0.95:  # Leave 5% cash
            final_size = (self.current_capital * 0.95) / entry_price
        
        return max(0.0, final_size)
    
    def _get_max_position_size(self, symbol: str, price: float) -> float:
        """Get maximum position size based on portfolio constraints"""
        
        # 1. Maximum single position (10% of portfolio)
        max_single_position = (self.current_capital * 0.1) / price
        
        # 2. Check sector exposure
        sector_exposure = self._calculate_sector_exposure(symbol)
        if sector_exposure >= self.max_sector_exposure:
            return 0.0
        
        # 3. Check correlation with existing positions
        correlation_penalty = self._calculate_correlation_penalty(symbol)
        max_correlation_position = max_single_position * (1 - correlation_penalty)
        
        return min(max_single_position, max_correlation_position)
    
    def _calculate_sector_exposure(self, symbol: str) -> float:
        """Calculate current sector exposure"""
        # This would need sector data from database
        # For now, return 0
        return 0.0
    
    def _calculate_correlation_penalty(self, symbol: str) -> float:
        """Calculate correlation penalty for position sizing"""
        # This would need correlation data
        # For now, return 0
        return 0.0
    
    def open_position(self, symbol: str, exchange: str, side: str, 
                     size: float, entry_price: float, stop_loss: float,
                     take_profit: float, signal_confidence: float) -> bool:
        """Open a new position"""
        
        # 1. Check if we can open position
        if not self._can_open_position(symbol, size, entry_price):
            return False
        
        # 2. Create position
        position = Position(
            symbol=symbol,
            exchange=exchange,
            side=side,
            size=size,
            entry_price=entry_price,
            current_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            entry_time=datetime.now(),
            unrealized_pnl=0.0,
            risk_amount=abs(entry_price - stop_loss) * size
        )
        
        # 3. Add to portfolio
        self.positions[symbol] = position
        
        # 4. Update capital
        self.current_capital -= size * entry_price
        
        # 5. Log trade
        self._log_trade('OPEN', symbol, side, size, entry_price, 0.0)
        
        logger.info(f"Opened {side} position: {symbol} {size} @ {entry_price}")
        return True
    
    def close_position(self, symbol: str, exit_price: float, reason: str = "manual") -> bool:
        """Close an existing position"""
        
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        
        # 1. Calculate P&L
        if position.side == 'long':
            pnl = (exit_price - position.entry_price) * position.size
        else:  # short
            pnl = (position.entry_price - exit_price) * position.size
        
        # 2. Update capital
        self.current_capital += position.size * exit_price
        
        # 3. Log trade
        self._log_trade('CLOSE', symbol, position.side, position.size, exit_price, pnl)
        
        # 4. Remove position
        del self.positions[symbol]
        
        # 5. Update daily returns
        self.daily_returns.append(pnl / self.initial_capital)
        
        logger.info(f"Closed {position.side} position: {symbol} @ {exit_price}, P&L: {pnl:.2f}")
        return True
    
    def update_positions(self, price_updates: Dict[str, float]):
        """Update current prices and P&L for all positions"""
        
        for symbol, position in self.positions.items():
            if symbol in price_updates:
                position.current_price = price_updates[symbol]
                
                # Calculate unrealized P&L
                if position.side == 'long':
                    position.unrealized_pnl = (position.current_price - position.entry_price) * position.size
                else:  # short
                    position.unrealized_pnl = (position.entry_price - position.current_price) * position.size
    
    def check_stop_losses(self, price_updates: Dict[str, float]) -> List[str]:
        """Check and close positions that hit stop loss"""
        
        closed_positions = []
        
        for symbol, position in self.positions.items():
            if symbol in price_updates:
                current_price = price_updates[symbol]
                
                # Check stop loss
                if position.side == 'long' and current_price <= position.stop_loss:
                    self.close_position(symbol, current_price, "stop_loss")
                    closed_positions.append(symbol)
                elif position.side == 'short' and current_price >= position.stop_loss:
                    self.close_position(symbol, current_price, "stop_loss")
                    closed_positions.append(symbol)
        
        return closed_positions
    
    def check_take_profits(self, price_updates: Dict[str, float]) -> List[str]:
        """Check and close positions that hit take profit"""
        
        closed_positions = []
        
        for symbol, position in self.positions.items():
            if symbol in price_updates:
                current_price = price_updates[symbol]
                
                # Check take profit
                if position.side == 'long' and current_price >= position.take_profit:
                    self.close_position(symbol, current_price, "take_profit")
                    closed_positions.append(symbol)
                elif position.side == 'short' and current_price <= position.take_profit:
                    self.close_position(symbol, current_price, "take_profit")
                    closed_positions.append(symbol)
        
        return closed_positions
    
    def _can_open_position(self, symbol: str, size: float, price: float) -> bool:
        """Check if we can open a new position"""
        
        # 1. Check if already have position
        if symbol in self.positions:
            return False
        
        # 2. Check maximum positions
        if len(self.positions) >= self.max_positions:
            return False
        
        # 3. Check available capital
        required_capital = size * price
        if required_capital > self.current_capital * 0.95:
            return False
        
        return True
    
    def _log_trade(self, action: str, symbol: str, side: str, 
                  size: float, price: float, pnl: float):
        """Log trade to history"""
        
        trade = {
            'timestamp': datetime.now(),
            'action': action,
            'symbol': symbol,
            'side': side,
            'size': size,
            'price': price,
            'pnl': pnl,
            'capital': self.current_capital
        }
        
        self.trade_history.append(trade)
    
    def get_portfolio_metrics(self) -> PortfolioMetrics:
        """Calculate portfolio performance metrics"""
        
        # 1. Total value
        total_value = self.current_capital
        for position in self.positions.values():
            total_value += position.unrealized_pnl
        
        # 2. Total P&L
        total_pnl = total_value - self.initial_capital
        total_pnl_pct = (total_pnl / self.initial_capital) * 100
        
        # 3. Daily P&L
        daily_pnl = sum(self.daily_returns[-1:]) if self.daily_returns else 0
        daily_pnl_pct = daily_pnl * 100
        
        # 4. Max drawdown
        max_drawdown = self._calculate_max_drawdown()
        
        # 5. Sharpe ratio
        sharpe_ratio = self._calculate_sharpe_ratio()
        
        # 6. Win rate and profit factor
        win_rate, avg_win, avg_loss, profit_factor = self._calculate_trade_stats()
        
        # 7. Risk metrics
        total_risk = sum(pos.risk_amount for pos in self.positions.values())
        
        return PortfolioMetrics(
            total_value=total_value,
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl_pct,
            daily_pnl=daily_pnl,
            daily_pnl_pct=daily_pnl_pct,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            total_trades=len(self.trade_history),
            open_positions=len(self.positions),
            risk_per_trade=self.risk_per_trade,
            total_risk=total_risk
        )
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        if not self.daily_returns:
            return 0.0
        
        cumulative = np.cumprod(1 + np.array(self.daily_returns))
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return abs(drawdown.min())
    
    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if not self.daily_returns or len(self.daily_returns) < 2:
            return 0.0
        
        returns = np.array(self.daily_returns)
        excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
        
        if returns.std() == 0:
            return 0.0
        
        return (excess_returns.mean() / returns.std()) * np.sqrt(252)
    
    def _calculate_trade_stats(self) -> Tuple[float, float, float, float]:
        """Calculate trade statistics"""
        if not self.trade_history:
            return 0.0, 0.0, 0.0, 0.0
        
        # Get closed trades only
        closed_trades = [t for t in self.trade_history if t['action'] == 'CLOSE']
        
        if not closed_trades:
            return 0.0, 0.0, 0.0, 0.0
        
        pnls = [t['pnl'] for t in closed_trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        
        win_rate = len(wins) / len(pnls) if pnls else 0.0
        avg_win = np.mean(wins) if wins else 0.0
        avg_loss = abs(np.mean(losses)) if losses else 0.0
        
        total_wins = sum(wins) if wins else 0.0
        total_losses = abs(sum(losses)) if losses else 0.0
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        return win_rate, avg_win, avg_loss, profit_factor
    
    def get_position_summary(self) -> Dict[str, Any]:
        """Get summary of all positions"""
        
        summary = {
            'total_positions': len(self.positions),
            'total_unrealized_pnl': sum(pos.unrealized_pnl for pos in self.positions.values()),
            'total_risk': sum(pos.risk_amount for pos in self.positions.values()),
            'positions': []
        }
        
        for symbol, position in self.positions.items():
            position_info = {
                'symbol': symbol,
                'side': position.side,
                'size': position.size,
                'entry_price': position.entry_price,
                'current_price': position.current_price,
                'unrealized_pnl': position.unrealized_pnl,
                'unrealized_pnl_pct': (position.unrealized_pnl / (position.entry_price * position.size)) * 100,
                'stop_loss': position.stop_loss,
                'take_profit': position.take_profit,
                'risk_amount': position.risk_amount
            }
            summary['positions'].append(position_info)
        
        return summary

# Global instance
portfolio_manager = PortfolioManager()
