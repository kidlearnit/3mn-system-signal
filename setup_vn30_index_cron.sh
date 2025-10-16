#!/bin/bash
# Setup VN30 Index hybrid signal engine cron job

echo "Setting up VN30 Index hybrid signal engine cron job..."

# Get current directory
PROJECT_DIR=$(pwd)

# Create cron entries for VN30 Index - VN market hours
CRON_ENTRIES="
# VN30 Index Hybrid Signal Engine - VN Market Hours
# Morning session
5,35 9 * * 1-5 cd $PROJECT_DIR && docker-compose exec market_monitor python vn30_index_job.py >> logs/vn30_index.log 2>&1
5,35 10 * * 1-5 cd $PROJECT_DIR && docker-compose exec market_monitor python vn30_index_job.py >> logs/vn30_index.log 2>&1
5 11 * * 1-5 cd $PROJECT_DIR && docker-compose exec market_monitor python vn30_index_job.py >> logs/vn30_index.log 2>&1

# Afternoon session
5,35 13 * * 1-5 cd $PROJECT_DIR && docker-compose exec market_monitor python vn30_index_job.py >> logs/vn30_index.log 2>&1
5,35 14 * * 1-5 cd $PROJECT_DIR && docker-compose exec market_monitor python vn30_index_job.py >> logs/vn30_index.log 2>&1
"

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_ENTRIES") | crontab -

echo "✅ VN30 Index cron job setup completed!"
echo "📅 VN30 Index Hybrid Signal Engine will run every 30 minutes during VN market hours"
echo "📊 Processing VN30 Index (VN-Index) with SMA + MACD analysis"
echo "📋 Check logs with: tail -f logs/vn30_index.log"
echo "📋 Check cron jobs with: crontab -l"
echo ""
echo "🚀 To test immediately:"
echo "   docker-compose exec market_monitor python vn30_index_job.py"
echo ""
echo "📈 VN30 Index Features:"
echo "   🎯 Single Symbol: VN30 Index (VN-Index)"
echo "   📊 SMA + MACD: Hybrid signal analysis"
echo "   ⏰ 3-Timeframe Analysis: 1m, 2m, 5m (focused on short-term)"
echo "   🎯 Market Sentiment: Bullish/Bearish/Neutral"
echo "   📈 Confidence Scoring: Signal reliability"
