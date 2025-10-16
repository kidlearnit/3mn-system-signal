#!/usr/bin/env python3
"""
Market Monitor Worker - Worker để chạy Market Signal Monitor
Tự động monitor thị trường và gửi tín hiệu từng mã riêng lẻ
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, time
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.market_signal_monitor import market_signal_monitor

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/market_monitor_worker.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class MarketMonitorWorker:
    """Worker để chạy Market Signal Monitor theo lịch"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.monitor = market_signal_monitor
        
        # Cấu hình lịch cho từng thị trường
        self.market_schedules = {
            'VN': {
                'timezone': 'Asia/Ho_Chi_Minh',
                'morning_jobs': [
                    {'hour': 9, 'minute': 5},   # 9:05 AM
                    {'hour': 9, 'minute': 35},  # 9:35 AM
                    {'hour': 10, 'minute': 5},  # 10:05 AM
                    {'hour': 10, 'minute': 35}, # 10:35 AM
                    {'hour': 11, 'minute': 5},  # 11:05 AM
                ],
                'afternoon_jobs': [
                    {'hour': 13, 'minute': 5},  # 1:05 PM
                    {'hour': 13, 'minute': 35}, # 1:35 PM
                    {'hour': 14, 'minute': 5},  # 2:05 PM
                    {'hour': 14, 'minute': 35}, # 2:35 PM
                ]
            },
            'US': {
                'timezone': 'America/New_York',
                'jobs': [
                    {'hour': 9, 'minute': 35},  # 9:35 AM
                    {'hour': 10, 'minute': 5},  # 10:05 AM
                    {'hour': 10, 'minute': 35}, # 10:35 AM
                    {'hour': 11, 'minute': 5},  # 11:05 AM
                    {'hour': 11, 'minute': 35}, # 11:35 AM
                    {'hour': 12, 'minute': 5},  # 12:05 PM
                    {'hour': 12, 'minute': 35}, # 12:35 PM
                    {'hour': 13, 'minute': 5},  # 1:05 PM
                    {'hour': 13, 'minute': 35}, # 1:35 PM
                    {'hour': 14, 'minute': 5},  # 2:05 PM
                    {'hour': 14, 'minute': 35}, # 2:35 PM
                    {'hour': 15, 'minute': 5},  # 3:05 PM
                ]
            }
        }
    
    def setup_scheduler(self):
        """Thiết lập lịch cho scheduler"""
        try:
            logger.info("📅 Setting up market monitoring schedules...")
            
            # Lịch cho thị trường VN
            vn_schedule = self.market_schedules['VN']
            
            # Phiên sáng VN (9:05 - 11:05)
            for job_config in vn_schedule['morning_jobs']:
                self.scheduler.add_job(
                    self.run_vn_monitoring,
                    CronTrigger(
                        hour=job_config['hour'],
                        minute=job_config['minute'],
                        timezone=vn_schedule['timezone']
                    ),
                    id=f"vn_morning_{job_config['hour']}_{job_config['minute']}",
                    name=f"VN Morning Monitoring {job_config['hour']}:{job_config['minute']:02d}"
                )
            
            # Phiên chiều VN (13:05 - 14:35)
            for job_config in vn_schedule['afternoon_jobs']:
                self.scheduler.add_job(
                    self.run_vn_monitoring,
                    CronTrigger(
                        hour=job_config['hour'],
                        minute=job_config['minute'],
                        timezone=vn_schedule['timezone']
                    ),
                    id=f"vn_afternoon_{job_config['hour']}_{job_config['minute']}",
                    name=f"VN Afternoon Monitoring {job_config['hour']}:{job_config['minute']:02d}"
                )
            
            # Lịch cho thị trường US
            us_schedule = self.market_schedules['US']
            
            for job_config in us_schedule['jobs']:
                self.scheduler.add_job(
                    self.run_us_monitoring,
                    CronTrigger(
                        hour=job_config['hour'],
                        minute=job_config['minute'],
                        timezone=us_schedule['timezone']
                    ),
                    id=f"us_{job_config['hour']}_{job_config['minute']}",
                    name=f"US Monitoring {job_config['hour']}:{job_config['minute']:02d}"
                )
            
            logger.info(f"✅ Scheduled {len(self.scheduler.get_jobs())} monitoring jobs")
            
            # Log tất cả jobs đã được schedule
            for job in self.scheduler.get_jobs():
                next_run = job.next_run_time if hasattr(job, 'next_run_time') else 'Unknown'
                logger.info(f"   📋 {job.name}: {next_run}")
            
        except Exception as e:
            logger.error(f"❌ Error setting up scheduler: {e}")
            raise
    
    async def run_vn_monitoring(self):
        """Chạy monitoring cho thị trường VN"""
        try:
            logger.info("🇻🇳 Starting VN market monitoring...")
            await self.monitor.monitor_market_signals('VN')
            logger.info("✅ VN market monitoring completed")
        except Exception as e:
            logger.error(f"❌ Error in VN monitoring: {e}")
    
    async def run_us_monitoring(self):
        """Chạy monitoring cho thị trường US"""
        try:
            logger.info("🇺🇸 Starting US market monitoring...")
            await self.monitor.monitor_market_signals('US')
            logger.info("✅ US market monitoring completed")
        except Exception as e:
            logger.error(f"❌ Error in US monitoring: {e}")
    
    async def run_manual_monitoring(self, market: str):
        """Chạy monitoring thủ công"""
        try:
            logger.info(f"🔧 Manual monitoring for {market} market...")
            await self.monitor.monitor_market_signals(market)
            logger.info(f"✅ Manual monitoring for {market} completed")
        except Exception as e:
            logger.error(f"❌ Error in manual monitoring for {market}: {e}")
    
    def start(self):
        """Bắt đầu worker"""
        try:
            logger.info("🚀 Starting Market Monitor Worker...")
            
            # Thiết lập scheduler
            self.setup_scheduler()
            
            # Bắt đầu scheduler
            self.scheduler.start()
            
            logger.info("✅ Market Monitor Worker started successfully")
            logger.info(f"📊 Monitoring {len(self.scheduler.get_jobs())} scheduled jobs")
            
        except Exception as e:
            logger.error(f"❌ Error starting Market Monitor Worker: {e}")
            raise
    
    def stop(self):
        """Dừng worker"""
        try:
            logger.info("🛑 Stopping Market Monitor Worker...")
            
            if self.scheduler.running:
                self.scheduler.shutdown()
            
            logger.info("✅ Market Monitor Worker stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping Market Monitor Worker: {e}")
    
    def get_status(self):
        """Lấy trạng thái worker"""
        try:
            status = {
                'running': self.scheduler.running,
                'jobs_count': len(self.scheduler.get_jobs()),
                'next_jobs': []
            }
            
            # Lấy 5 jobs tiếp theo
            jobs = self.scheduler.get_jobs()
            for job in jobs[:5]:
                next_run = getattr(job, 'next_run_time', None)
                status['next_jobs'].append({
                    'name': job.name,
                    'next_run': next_run.isoformat() if next_run else None
                })
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Error getting worker status: {e}")
            return {'error': str(e)}

async def main():
    """Hàm chính để chạy worker"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Market Monitor Worker')
    parser.add_argument('--market', choices=['VN', 'US'], 
                       help='Run manual monitoring for specific market')
    parser.add_argument('--status', action='store_true', 
                       help='Show worker status')
    
    args = parser.parse_args()
    
    # Tạo thư mục logs nếu chưa có
    os.makedirs('logs', exist_ok=True)
    
    worker = MarketMonitorWorker()
    
    try:
        if args.status:
            # Hiển thị trạng thái
            status = worker.get_status()
            print("📊 Market Monitor Worker Status:")
            print(f"   Running: {status.get('running', False)}")
            print(f"   Jobs Count: {status.get('jobs_count', 0)}")
            print("   Next Jobs:")
            for job in status.get('next_jobs', []):
                print(f"      - {job['name']}: {job['next_run']}")
        
        elif args.market:
            # Chạy monitoring thủ công
            await worker.run_manual_monitoring(args.market)
        
        else:
            # Chạy worker với scheduler
            worker.start()
            
            logger.info("🎯 Market Monitor Worker is running...")
            logger.info("Press Ctrl+C to stop")
            
            # Giữ worker chạy
            try:
                while True:
                    await asyncio.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("🛑 Received interrupt signal")
    
    except Exception as e:
        logger.error(f"❌ Error in main: {e}")
    finally:
        worker.stop()

if __name__ == "__main__":
    asyncio.run(main())
