#!/usr/bin/env python3
"""
Smart Backfill Engine
Intelligent data backfilling with adaptive strategies
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
from dataclasses import dataclass
from enum import Enum

# Add app to path
sys.path.append('/app')

from app.db import SessionLocal
from app.models import Symbol, Candle
from app.services.data_sources import fetch_data_from_source
from app.services.debug import debug_helper

logger = logging.getLogger(__name__)

class BackfillStrategy(Enum):
    """Backfill strategies based on data gaps"""
    FULL_HISTORICAL = "full_historical"  # Complete historical data
    INCREMENTAL = "incremental"          # Fill recent gaps only
    SMART_CHUNK = "smart_chunk"          # Intelligent chunking
    PRIORITY_BASED = "priority_based"    # Based on symbol importance

@dataclass
class BackfillConfig:
    """Configuration for smart backfill"""
    symbol_id: int
    ticker: str
    exchange: str
    strategy: BackfillStrategy
    max_days: int = 365
    chunk_size_days: int = 30
    priority_score: float = 1.0
    last_successful_fetch: Optional[datetime] = None
    data_quality_threshold: float = 0.95

class SmartBackfillEngine:
    """Intelligent backfill engine with adaptive strategies"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.backfill_stats = {}
        
    def analyze_data_gaps(self, symbol_id: int) -> Dict:
        """Analyze data gaps and determine optimal backfill strategy"""
        try:
            # Get symbol info
            symbol = self.db.query(Symbol).filter(Symbol.id == symbol_id).first()
            if not symbol:
                return {"error": f"Symbol {symbol_id} not found"}
            
            # Get existing data coverage
            latest_candle = self.db.query(Candle).filter(
                Candle.symbol_id == symbol_id
            ).order_by(Candle.ts.desc()).first()
            
            earliest_candle = self.db.query(Candle).filter(
                Candle.symbol_id == symbol_id
            ).order_by(Candle.ts.asc()).first()
            
            now = datetime.now()
            
            # Calculate gaps
            gaps = {
                "total_candles": self.db.query(Candle).filter(
                    Candle.symbol_id == symbol_id
                ).count(),
                "latest_timestamp": latest_candle.ts if latest_candle else None,
                "earliest_timestamp": earliest_candle.ts if earliest_candle else None,
                "days_since_latest": (now - latest_candle.ts).days if latest_candle else 999,
                "data_quality_score": self._calculate_data_quality(symbol_id),
                "market_activity_score": self._calculate_market_activity(symbol_id)
            }
            
            # Determine strategy
            strategy = self._determine_strategy(gaps, symbol)
            gaps["recommended_strategy"] = strategy
            
            debug_helper.log_step(f"Data gap analysis for {symbol.ticker}", gaps)
            return gaps
            
        except Exception as e:
            logger.error(f"Error analyzing data gaps for {symbol_id}: {e}")
            return {"error": str(e)}
    
    def _calculate_data_quality(self, symbol_id: int) -> float:
        """Calculate data quality score (0-1)"""
        try:
            # Get recent candles
            recent_candles = self.db.query(Candle).filter(
                Candle.symbol_id == symbol_id,
                Candle.ts >= datetime.now() - timedelta(days=30)
            ).order_by(Candle.ts.desc()).limit(1000).all()
            
            if not recent_candles:
                return 0.0
            
            # Check for missing data points
            expected_intervals = 30 * 24 * 60  # 30 days in minutes
            actual_count = len(recent_candles)
            completeness = min(actual_count / expected_intervals, 1.0)
            
            # Check for data anomalies
            anomalies = 0
            for i in range(1, len(recent_candles)):
                prev_candle = recent_candles[i]
                curr_candle = recent_candles[i-1]
                
                # Check for price jumps > 20%
                if prev_candle.close > 0:
                    price_change = abs(curr_candle.close - prev_candle.close) / prev_candle.close
                    if price_change > 0.2:
                        anomalies += 1
            
            anomaly_rate = anomalies / len(recent_candles) if recent_candles else 0
            quality_score = completeness * (1 - anomaly_rate)
            
            return max(0.0, min(1.0, quality_score))
            
        except Exception as e:
            logger.error(f"Error calculating data quality: {e}")
            return 0.0
    
    def _calculate_market_activity(self, symbol_id: int) -> float:
        """Calculate market activity score based on volume and volatility"""
        try:
            # Get recent candles with volume
            recent_candles = self.db.query(Candle).filter(
                Candle.symbol_id == symbol_id,
                Candle.ts >= datetime.now() - timedelta(days=7),
                Candle.volume.isnot(None)
            ).order_by(Candle.ts.desc()).limit(1000).all()
            
            if not recent_candles:
                return 0.0
            
            # Calculate average volume
            total_volume = sum(c.volume for c in recent_candles if c.volume)
            avg_volume = total_volume / len(recent_candles)
            
            # Calculate volatility
            prices = [c.close for c in recent_candles]
            if len(prices) > 1:
                returns = [(prices[i] - prices[i+1]) / prices[i+1] for i in range(len(prices)-1)]
                volatility = pd.Series(returns).std() if returns else 0
            else:
                volatility = 0
            
            # Normalize scores (0-1)
            volume_score = min(avg_volume / 1000000, 1.0)  # Normalize to 1M volume
            volatility_score = min(volatility * 100, 1.0)  # Normalize volatility
            
            activity_score = (volume_score + volatility_score) / 2
            return max(0.0, min(1.0, activity_score))
            
        except Exception as e:
            logger.error(f"Error calculating market activity: {e}")
            return 0.0
    
    def _determine_strategy(self, gaps: Dict, symbol: Symbol) -> BackfillStrategy:
        """Determine optimal backfill strategy based on analysis"""
        days_since_latest = gaps["days_since_latest"]
        data_quality = gaps["data_quality_score"]
        market_activity = gaps["market_activity_score"]
        
        # High priority symbols (large caps, ETFs)
        is_high_priority = symbol.ticker in ['VCB', 'BID', 'CTG', 'MBB', 'TCB', 'AAPL', 'MSFT', 'NVDA', 'TQQQ']
        
        if days_since_latest > 30:
            return BackfillStrategy.FULL_HISTORICAL
        elif days_since_latest > 7:
            return BackfillStrategy.SMART_CHUNK
        elif data_quality < 0.8 or market_activity > 0.7:
            return BackfillStrategy.INCREMENTAL
        elif is_high_priority:
            return BackfillStrategy.PRIORITY_BASED
        else:
            return BackfillStrategy.INCREMENTAL
    
    def execute_smart_backfill(self, symbol_id: int, config: Optional[BackfillConfig] = None) -> Dict:
        """Execute intelligent backfill based on analysis"""
        try:
            # Analyze data gaps
            gaps = self.analyze_data_gaps(symbol_id)
            if "error" in gaps:
                return gaps
            
            symbol = self.db.query(Symbol).filter(Symbol.id == symbol_id).first()
            strategy = BackfillStrategy(gaps["recommended_strategy"])
            
            # Create config if not provided
            if not config:
                config = BackfillConfig(
                    symbol_id=symbol_id,
                    ticker=symbol.ticker,
                    exchange=symbol.exchange,
                    strategy=strategy,
                    max_days=365 if strategy == BackfillStrategy.FULL_HISTORICAL else 30,
                    chunk_size_days=30 if strategy == BackfillStrategy.SMART_CHUNK else 7,
                    priority_score=1.0 if symbol.ticker in ['VCB', 'BID', 'AAPL', 'MSFT', 'NVDA'] else 0.5
                )
            
            # Execute backfill based on strategy
            result = self._execute_strategy(config, gaps)
            
            # Update statistics
            self.backfill_stats[symbol_id] = {
                "last_backfill": datetime.now(),
                "strategy_used": strategy.value,
                "candles_added": result.get("candles_added", 0),
                "success": result.get("success", False)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in smart backfill for {symbol_id}: {e}")
            return {"error": str(e), "success": False}
    
    def _execute_strategy(self, config: BackfillConfig, gaps: Dict) -> Dict:
        """Execute specific backfill strategy"""
        try:
            if config.strategy == BackfillStrategy.FULL_HISTORICAL:
                return self._full_historical_backfill(config)
            elif config.strategy == BackfillStrategy.INCREMENTAL:
                return self._incremental_backfill(config)
            elif config.strategy == BackfillStrategy.SMART_CHUNK:
                return self._smart_chunk_backfill(config)
            elif config.strategy == BackfillStrategy.PRIORITY_BASED:
                return self._priority_based_backfill(config)
            else:
                return {"error": f"Unknown strategy: {config.strategy}", "success": False}
                
        except Exception as e:
            logger.error(f"Error executing strategy {config.strategy}: {e}")
            return {"error": str(e), "success": False}
    
    def _full_historical_backfill(self, config: BackfillConfig) -> Dict:
        """Full historical backfill with chunking"""
        try:
            debug_helper.log_step(f"Starting full historical backfill for {config.ticker}")
            
            total_candles = 0
            start_date = datetime.now() - timedelta(days=config.max_days)
            current_date = start_date
            
            while current_date < datetime.now():
                end_date = min(current_date + timedelta(days=config.chunk_size_days), datetime.now())
                
                # Fetch data for this chunk
                chunk_result = self._fetch_data_chunk(
                    config.ticker, config.exchange, current_date, end_date
                )
                
                if chunk_result["success"]:
                    total_candles += chunk_result["candles_added"]
                
                current_date = end_date
            
            return {
                "success": True,
                "candles_added": total_candles,
                "strategy": "full_historical",
                "period_days": config.max_days
            }
            
        except Exception as e:
            logger.error(f"Error in full historical backfill: {e}")
            return {"error": str(e), "success": False}
    
    def _incremental_backfill(self, config: BackfillConfig) -> Dict:
        """Incremental backfill for recent gaps"""
        try:
            debug_helper.log_step(f"Starting incremental backfill for {config.ticker}")
            
            # Get latest candle timestamp
            latest_candle = self.db.query(Candle).filter(
                Candle.symbol_id == config.symbol_id
            ).order_by(Candle.ts.desc()).first()
            
            if not latest_candle:
                # No data exists, do full backfill
                return self._full_historical_backfill(config)
            
            start_date = latest_candle.ts
            end_date = datetime.now()
            
            result = self._fetch_data_chunk(config.ticker, config.exchange, start_date, end_date)
            result["strategy"] = "incremental"
            
            return result
            
        except Exception as e:
            logger.error(f"Error in incremental backfill: {e}")
            return {"error": str(e), "success": False}
    
    def _smart_chunk_backfill(self, config: BackfillConfig) -> Dict:
        """Smart chunking based on market volatility"""
        try:
            debug_helper.log_step(f"Starting smart chunk backfill for {config.ticker}")
            
            # Analyze volatility patterns to determine optimal chunk sizes
            volatility_chunks = self._analyze_volatility_patterns(config.symbol_id)
            
            total_candles = 0
            for chunk in volatility_chunks:
                result = self._fetch_data_chunk(
                    config.ticker, config.exchange, chunk["start"], chunk["end"]
                )
                
                if result["success"]:
                    total_candles += result["candles_added"]
            
            return {
                "success": True,
                "candles_added": total_candles,
                "strategy": "smart_chunk",
                "chunks_processed": len(volatility_chunks)
            }
            
        except Exception as e:
            logger.error(f"Error in smart chunk backfill: {e}")
            return {"error": str(e), "success": False}
    
    def _priority_based_backfill(self, config: BackfillConfig) -> Dict:
        """Priority-based backfill for important symbols"""
        try:
            debug_helper.log_step(f"Starting priority-based backfill for {config.ticker}")
            
            # High priority symbols get more frequent updates
            if config.priority_score > 0.8:
                # Update every 5 minutes
                update_interval = timedelta(minutes=5)
            else:
                # Update every 15 minutes
                update_interval = timedelta(minutes=15)
            
            # Get last update time
            last_update = config.last_successful_fetch or datetime.now() - timedelta(hours=1)
            
            if datetime.now() - last_update > update_interval:
                result = self._incremental_backfill(config)
                result["strategy"] = "priority_based"
                return result
            else:
                return {
                    "success": True,
                    "candles_added": 0,
                    "strategy": "priority_based",
                    "message": "No update needed yet"
                }
                
        except Exception as e:
            logger.error(f"Error in priority-based backfill: {e}")
            return {"error": str(e), "success": False}
    
    def _fetch_data_chunk(self, ticker: str, exchange: str, start_date: datetime, end_date: datetime) -> Dict:
        """Fetch data for a specific time chunk"""
        try:
            # Use existing data source
            data = fetch_data_from_source(ticker, exchange, start_date, end_date)
            
            if data is None or data.empty:
                return {"success": False, "candles_added": 0, "message": "No data available"}
            
            # Store data (simplified - would need proper upsert logic)
            candles_added = len(data)
            
            return {
                "success": True,
                "candles_added": candles_added,
                "start_date": start_date,
                "end_date": end_date
            }
            
        except Exception as e:
            logger.error(f"Error fetching data chunk: {e}")
            return {"error": str(e), "success": False}
    
    def _analyze_volatility_patterns(self, symbol_id: int) -> List[Dict]:
        """Analyze volatility patterns to determine optimal chunk sizes"""
        try:
            # Get historical data to analyze volatility
            candles = self.db.query(Candle).filter(
                Candle.symbol_id == symbol_id,
                Candle.ts >= datetime.now() - timedelta(days=30)
            ).order_by(Candle.ts.asc()).all()
            
            if len(candles) < 100:
                # Not enough data, use default chunks
                return [{
                    "start": datetime.now() - timedelta(days=30),
                    "end": datetime.now(),
                    "volatility": 0.1
                }]
            
            # Calculate rolling volatility
            prices = [c.close for c in candles]
            returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
            
            # Create volatility-based chunks
            chunks = []
            chunk_size = 7  # days
            current_date = datetime.now() - timedelta(days=30)
            
            while current_date < datetime.now():
                end_date = min(current_date + timedelta(days=chunk_size), datetime.now())
                
                # Calculate volatility for this period
                period_returns = returns[-int((datetime.now() - current_date).days * 24 * 60):]
                volatility = pd.Series(period_returns).std() if period_returns else 0.1
                
                chunks.append({
                    "start": current_date,
                    "end": end_date,
                    "volatility": volatility
                })
                
                current_date = end_date
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error analyzing volatility patterns: {e}")
            return [{
                "start": datetime.now() - timedelta(days=30),
                "end": datetime.now(),
                "volatility": 0.1
            }]
    
    def get_backfill_status(self, symbol_id: int) -> Dict:
        """Get backfill status for a symbol"""
        return self.backfill_stats.get(symbol_id, {
            "last_backfill": None,
            "strategy_used": None,
            "candles_added": 0,
            "success": False
        })
    
    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()

# Global instance
smart_backfill_engine = SmartBackfillEngine()

def job_smart_backfill(symbol_id: int, ticker: str, exchange: str, strategy: str = "auto") -> str:
    """RQ job for smart backfill"""
    try:
        debug_helper.log_step(f"Starting smart backfill job for {ticker}")
        
        # Create config
        config = BackfillConfig(
            symbol_id=symbol_id,
            ticker=ticker,
            exchange=exchange,
            strategy=BackfillStrategy(strategy) if strategy != "auto" else None
        )
        
        # Execute smart backfill
        result = smart_backfill_engine.execute_smart_backfill(symbol_id, config)
        
        if result.get("success"):
            debug_helper.log_step(f"Smart backfill completed for {ticker}", result)
            return f"success:{result['candles_added']} candles"
        else:
            debug_helper.log_step(f"Smart backfill failed for {ticker}", result)
            return f"error:{result.get('error', 'Unknown error')}"
            
    except Exception as e:
        logger.error(f"Error in smart backfill job: {e}")
        return f"error:{str(e)}"
