#!/usr/bin/env python3
"""
Script để chạy Market Signal Monitor
Sử dụng Hybrid Signal Engine để monitor thị trường và gửi tín hiệu từng mã riêng lẻ
"""

import sys
import os
import asyncio
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.market_signal_monitor import market_signal_monitor

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/market_monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def run_single_monitoring(market: str = 'VN'):
    """Chạy monitoring một lần"""
    try:
        logger.info(f"🚀 Starting single market monitoring for {market}")
        logger.info(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Kiểm tra thị trường có mở cửa không
        if not market_signal_monitor.is_market_open(market):
            logger.info(f"❌ Market {market} is currently closed")
            return
        
        logger.info(f"✅ Market {market} is open, starting monitoring...")
        
        # Chạy monitoring
        await market_signal_monitor.monitor_market_signals(market)
        
        logger.info("✅ Single monitoring completed")
        
    except Exception as e:
        logger.error(f"❌ Error in single monitoring: {e}")

async def run_continuous_monitoring(market: str = 'VN', interval_minutes: int = 5):
    """Chạy monitoring liên tục"""
    try:
        logger.info(f"🚀 Starting continuous market monitoring for {market}")
        logger.info(f"⏰ Interval: {interval_minutes} minutes")
        logger.info(f"📅 Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        await market_signal_monitor.run_continuous_monitoring(market, interval_minutes)
        
    except KeyboardInterrupt:
        logger.info("🛑 Monitoring stopped by user")
    except Exception as e:
        logger.error(f"❌ Error in continuous monitoring: {e}")

async def test_market_status():
    """Test trạng thái thị trường"""
    logger.info("🔍 Testing market status...")
    
    markets = ['VN', 'US']
    for market in markets:
        is_open = market_signal_monitor.is_market_open(market)
        status = "🟢 OPEN" if is_open else "🔴 CLOSED"
        logger.info(f"   {market} Market: {status}")
    
    # Test lấy symbols
    logger.info("📊 Testing symbol retrieval...")
    for market in markets:
        symbols = market_signal_monitor.get_active_symbols(market)
        logger.info(f"   {market} Market: {len(symbols)} active symbols")
        if symbols:
            logger.info(f"      Sample: {[s['ticker'] for s in symbols[:5]]}")

async def main():
    """Hàm chính"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Market Signal Monitor')
    parser.add_argument('--market', default='VN', choices=['VN', 'US'], 
                       help='Market to monitor (default: VN)')
    parser.add_argument('--mode', default='single', choices=['single', 'continuous'], 
                       help='Monitoring mode (default: single)')
    parser.add_argument('--interval', type=int, default=5, 
                       help='Interval in minutes for continuous mode (default: 5)')
    parser.add_argument('--test', action='store_true', 
                       help='Test market status and symbol retrieval')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("🎯 MARKET SIGNAL MONITOR")
    logger.info("=" * 60)
    logger.info(f"Market: {args.market}")
    logger.info(f"Mode: {args.mode}")
    if args.mode == 'continuous':
        logger.info(f"Interval: {args.interval} minutes")
    logger.info("=" * 60)
    
    try:
        if args.test:
            await test_market_status()
        elif args.mode == 'single':
            await run_single_monitoring(args.market)
        elif args.mode == 'continuous':
            await run_continuous_monitoring(args.market, args.interval)
        
    except KeyboardInterrupt:
        logger.info("🛑 Program interrupted by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    finally:
        logger.info("👋 Market Signal Monitor stopped")

if __name__ == "__main__":
    # Tạo thư mục logs nếu chưa có
    os.makedirs('logs', exist_ok=True)
    
    # Chạy chương trình
    asyncio.run(main())
