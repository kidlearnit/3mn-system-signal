#!/usr/bin/env python3
"""
VN30 Index Realtime Job
Chạy realtime khi thị trường mở cửa, chỉ tính chỉ báo khi có dữ liệu mới
"""

import os
import sys
import asyncio
import logging
import time
from datetime import datetime, timedelta
import pytz

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/vn30_realtime.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# VN30 Index symbol
VN30_INDEX = {
    'id': 1,  # VN30 Index ID
    'ticker': 'VN30',
    'name': 'VN30 Index',
    'exchange': 'HOSE'
}

# VN Market hours (UTC+7)
VN_MARKET_OPEN = "09:00"
VN_MARKET_CLOSE = "15:00"

class VN30RealtimeJob:
    """VN30 Index Realtime Job Class"""
    
    def __init__(self):
        self.hybrid_signal_engine = None
        self.last_data_timestamp = {}
        self.is_running = False
        
    async def initialize(self):
        """Initialize the job"""
        try:
            # Initialize database
            from app.db import init_db
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                init_db(database_url)
                logger.info("✅ Database initialized")
            
            # Import hybrid signal engine
            from app.services.hybrid_signal_engine import hybrid_signal_engine
            self.hybrid_signal_engine = hybrid_signal_engine
            logger.info("✅ Hybrid Signal Engine initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error initializing VN30 Realtime Job: {e}")
            return False
    
    def is_market_open(self):
        """Check if VN market is open"""
        try:
            # Get current time in VN timezone
            vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
            now = datetime.now(vn_tz)
            current_time = now.strftime("%H:%M")
            current_weekday = now.weekday()  # 0=Monday, 6=Sunday
            
            # Check if it's a weekday (Monday=0 to Friday=4)
            if current_weekday >= 5:  # Saturday or Sunday
                return False
            
            # Check if it's within market hours
            if VN_MARKET_OPEN <= current_time <= VN_MARKET_CLOSE:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking market hours: {e}")
            return False
    
    def has_new_data(self, timeframe):
        """Check if there's new data for the timeframe"""
        try:
            from app.db import SessionLocal
            from sqlalchemy import text
            
            with SessionLocal() as s:
                # Get latest candle timestamp for the timeframe
                result = s.execute(text("""
                    SELECT MAX(ts) as latest_ts
                    FROM candles_tf
                    WHERE symbol_id = :symbol_id AND timeframe = :timeframe
                """), {
                    'symbol_id': VN30_INDEX['id'],
                    'timeframe': timeframe
                }).fetchone()
                
                if result and result[0]:
                    latest_ts = result[0]
                    
                    # Check if this is newer than our last check
                    if timeframe not in self.last_data_timestamp:
                        self.last_data_timestamp[timeframe] = latest_ts
                        return True
                    
                    if latest_ts > self.last_data_timestamp[timeframe]:
                        self.last_data_timestamp[timeframe] = latest_ts
                        return True
                
                return False
                
        except Exception as e:
            logger.error(f"❌ Error checking new data for {timeframe}: {e}")
            return False
    
    async def process_timeframe(self, timeframe):
        """Process a single timeframe if there's new data"""
        try:
            if not self.has_new_data(timeframe):
                logger.debug(f"⏳ No new data for {timeframe}, skipping...")
                return None
            
            logger.info(f"🔄 Processing {timeframe} with new data...")
            
            # Get hybrid signal for this timeframe
            result = self.hybrid_signal_engine.evaluate_hybrid_signal(
                VN30_INDEX['id'], 
                VN30_INDEX['ticker'], 
                VN30_INDEX['exchange'], 
                timeframe
            )
            
            if result:
                signal = result.get('hybrid_signal', 'UNKNOWN')
                confidence = result.get('confidence', 0.0)
                direction = result.get('hybrid_direction', 'UNKNOWN')
                
                logger.info(f"📈 {VN30_INDEX['ticker']} {timeframe}: {signal} ({direction}) - Confidence: {confidence:.2f}")
                
                return {
                    'timeframe': timeframe,
                    'signal': str(signal).split('.')[-1],
                    'confidence': confidence,
                    'direction': direction,
                    'timestamp': datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error processing {timeframe}: {e}")
            return None
    
    async def run_cycle(self):
        """Run one cycle of the realtime job"""
        try:
            if not self.is_market_open():
                logger.debug("⏳ Market is closed, waiting...")
                return
            
            logger.info("🔄 VN30 Realtime Cycle Started")
            
            # Process 3 timeframes: 1m, 2m, 5m
            timeframes = ['1m', '2m', '5m']
            results = []
            
            for tf in timeframes:
                result = await self.process_timeframe(tf)
                if result:
                    results.append(result)
            
            if results:
                # Calculate overall signal from results
                confidences = [r['confidence'] for r in results]
                directions = [r['direction'] for r in results]
                
                overall_confidence = sum(confidences) / len(confidences)
                direction_counts = {}
                for direction in directions:
                    direction_counts[direction] = direction_counts.get(direction, 0) + 1
                overall_direction = max(direction_counts, key=direction_counts.get)
                
                # Determine overall signal
                if overall_confidence > 0.6:
                    if overall_direction == 'BULLISH':
                        overall_signal = 'STRONG_BUY'
                    elif overall_direction == 'BEARISH':
                        overall_signal = 'STRONG_SELL'
                    else:
                        overall_signal = 'NEUTRAL'
                elif overall_confidence > 0.3:
                    if overall_direction == 'BULLISH':
                        overall_signal = 'BUY'
                    elif overall_direction == 'BEARISH':
                        overall_signal = 'SELL'
                    else:
                        overall_signal = 'NEUTRAL'
                else:
                    overall_signal = 'NEUTRAL'
                
                # Log summary
                logger.info("📊 VN30 REALTIME SUMMARY:")
                for result in results:
                    logger.info(f"   📈 {result['timeframe']}: {result['signal']} ({result['direction']}) - Confidence: {result['confidence']:.2f}")
                
                logger.info(f"   📊 Overall: {overall_signal} ({overall_direction}) - Confidence: {overall_confidence:.2f}")
                
                # Signal strength analysis
                if overall_confidence > 0.7:
                    logger.info(f"🚨 STRONG SIGNAL DETECTED: {overall_signal} (Confidence: {overall_confidence:.2f})")
                elif overall_confidence > 0.5:
                    logger.info(f"📊 MODERATE SIGNAL: {overall_signal} (Confidence: {overall_confidence:.2f})")
                else:
                    logger.info(f"➡️ WEAK SIGNAL: {overall_signal} (Confidence: {overall_confidence:.2f})")
                
            else:
                logger.info("⏳ No new data to process in this cycle")
            
            logger.info("✅ VN30 Realtime Cycle Completed")
            
        except Exception as e:
            logger.error(f"❌ Error in realtime cycle: {e}")
    
    async def run(self, cycle_interval=30):
        """Run the realtime job"""
        try:
            logger.info("🚀 VN30 Index Realtime Job Started")
            logger.info(f"📊 Processing: {VN30_INDEX['ticker']} - {VN30_INDEX['name']}")
            logger.info(f"⏰ Timeframes: 1m, 2m, 5m")
            logger.info(f"🔄 Cycle Interval: {cycle_interval} seconds")
            logger.info(f"📅 VN Market Hours: {VN_MARKET_OPEN} - {VN_MARKET_CLOSE} (UTC+7)")
            
            self.is_running = True
            
            while self.is_running:
                try:
                    await self.run_cycle()
                    
                    # Wait for next cycle
                    await asyncio.sleep(cycle_interval)
                    
                except KeyboardInterrupt:
                    logger.info("🛑 Received interrupt signal, stopping...")
                    break
                except Exception as e:
                    logger.error(f"❌ Error in main loop: {e}")
                    await asyncio.sleep(cycle_interval)
            
            logger.info("✅ VN30 Index Realtime Job Stopped")
            
        except Exception as e:
            logger.error(f"❌ Error running VN30 Realtime Job: {e}")
    
    def stop(self):
        """Stop the realtime job"""
        self.is_running = False

async def main():
    """Main function"""
    job = VN30RealtimeJob()
    
    # Initialize
    if not await job.initialize():
        logger.error("❌ Failed to initialize VN30 Realtime Job")
        return
    
    # Run the job
    await job.run(cycle_interval=30)  # 30 seconds cycle

if __name__ == "__main__":
    asyncio.run(main())
