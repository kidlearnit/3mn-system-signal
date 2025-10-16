#!/usr/bin/env python3
"""
VN30 Index Hybrid Signal Engine Job
Chạy hybrid signal engine chỉ cho VN30 Index (VN-Index)
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/vn30_index.log'),
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

async def vn30_index_job():
    """VN30 Index Hybrid Signal Engine Job"""
    try:
        logger.info("🚀 VN30 Index Hybrid Signal Engine Job Started")
        logger.info(f"📊 Processing VN30 Index: {VN30_INDEX['ticker']} - {VN30_INDEX['name']}")
        
        # Initialize database
        from app.db import init_db
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            init_db(database_url)
            logger.info("✅ Database initialized")
        
        # Import after database init
        from app.services.hybrid_signal_engine import hybrid_signal_engine
        
        # Process VN30 Index
        try:
            logger.info(f"🔍 Processing {VN30_INDEX['ticker']} - {VN30_INDEX['name']}")
            
            # Get hybrid signal for 5m timeframe
            result = hybrid_signal_engine.evaluate_hybrid_signal(
                VN30_INDEX['id'], 
                VN30_INDEX['ticker'], 
                VN30_INDEX['exchange'], 
                '5m'
            )
            
            signal = result.get('hybrid_signal', 'UNKNOWN')
            confidence = result.get('confidence', 0)
            direction = result.get('hybrid_direction', 'UNKNOWN')
            
            # Get multi-timeframe analysis for 3 timeframes: 1m, 2m, 5m
            timeframes = ['1m', '2m', '5m']
            timeframe_results = {}
            
            for tf in timeframes:
                tf_result = hybrid_signal_engine.evaluate_hybrid_signal(
                    VN30_INDEX['id'], 
                    VN30_INDEX['ticker'], 
                    VN30_INDEX['exchange'], 
                    tf
                )
                timeframe_results[tf] = tf_result
                
            # Aggregate results from 3 timeframes
            result_multi = {
                'timeframe_results': timeframe_results,
                'overall_signal': 'NEUTRAL',
                'overall_confidence': 0.0,
                'overall_direction': 'NEUTRAL'
            }
            
            # Calculate overall signal from 3 timeframes
            signals = []
            confidences = []
            directions = []
            
            for tf, tf_result in timeframe_results.items():
                if tf_result and tf_result.get('hybrid_signal'):
                    signal = str(tf_result['hybrid_signal']).split('.')[-1]  # Get signal name
                    confidence = tf_result.get('confidence', 0.0)
                    direction = tf_result.get('hybrid_direction', 'NEUTRAL')
                    
                    signals.append(signal)
                    confidences.append(confidence)
                    directions.append(direction)
                    
                    logger.info(f"📈 {VN30_INDEX['ticker']} {tf} Signal: {signal} ({direction}) - Confidence: {confidence:.2f}")
            
            if signals:
                # Calculate overall confidence (average)
                result_multi['overall_confidence'] = sum(confidences) / len(confidences)
                
                # Determine overall direction (majority vote)
                direction_counts = {}
                for direction in directions:
                    direction_counts[direction] = direction_counts.get(direction, 0) + 1
                
                result_multi['overall_direction'] = max(direction_counts, key=direction_counts.get)
                
                # Determine overall signal based on direction and confidence
                if result_multi['overall_confidence'] > 0.6:
                    if result_multi['overall_direction'] == 'BULLISH':
                        result_multi['overall_signal'] = 'STRONG_BUY'
                    elif result_multi['overall_direction'] == 'BEARISH':
                        result_multi['overall_signal'] = 'STRONG_SELL'
                    else:
                        result_multi['overall_signal'] = 'NEUTRAL'
                elif result_multi['overall_confidence'] > 0.3:
                    if result_multi['overall_direction'] == 'BULLISH':
                        result_multi['overall_signal'] = 'BUY'
                    elif result_multi['overall_direction'] == 'BEARISH':
                        result_multi['overall_signal'] = 'SELL'
                    else:
                        result_multi['overall_signal'] = 'NEUTRAL'
                else:
                    result_multi['overall_signal'] = 'NEUTRAL'
            
            overall_signal = result_multi.get('overall_signal', 'UNKNOWN')
            overall_confidence = result_multi.get('overall_confidence', 0)
            overall_direction = result_multi.get('overall_direction', 'UNKNOWN')
            
            # Log results
            logger.info(f"📈 VN30 Index 5m Signal: {signal} ({direction}) - Confidence: {confidence:.2f}")
            logger.info(f"📊 VN30 Index Multi-timeframe: {overall_signal} ({overall_direction}) - Confidence: {overall_confidence:.2f}")
            
            # Signal strength analysis
            if confidence > 0.7:
                logger.info(f"🚨 STRONG SIGNAL: VN30 Index - {signal} (Confidence: {confidence:.2f})")
            elif confidence > 0.5:
                logger.info(f"📊 MODERATE SIGNAL: VN30 Index - {signal} (Confidence: {confidence:.2f})")
            else:
                logger.info(f"➡️ WEAK SIGNAL: VN30 Index - {signal} (Confidence: {confidence:.2f})")
            
            # Market sentiment
            if 'BUY' in str(signal):
                logger.info("📈 VN30 Index: BULLISH MARKET SENTIMENT")
            elif 'SELL' in str(signal):
                logger.info("📉 VN30 Index: BEARISH MARKET SENTIMENT")
            else:
                logger.info("➡️ VN30 Index: NEUTRAL MARKET SENTIMENT")
            
            # Summary
            logger.info("📊 VN30 INDEX SUMMARY:")
            logger.info(f"   📈 5m Signal: {signal} ({direction}) - Confidence: {confidence:.2f}")
            logger.info(f"   📊 3-Timeframe Analysis (1m, 2m, 5m): {overall_signal} ({overall_direction}) - Confidence: {overall_confidence:.2f}")
            logger.info(f"   🎯 Market Sentiment: {'BULLISH' if 'BUY' in str(signal) else 'BEARISH' if 'SELL' in str(signal) else 'NEUTRAL'}")
            
        except Exception as e:
            logger.error(f"❌ Error processing VN30 Index: {e}")
        
        logger.info("✅ VN30 Index Hybrid Signal Engine Job Completed")
        
    except Exception as e:
        logger.error(f"❌ Error in VN30 Index job: {e}")

if __name__ == "__main__":
    asyncio.run(vn30_index_job())
