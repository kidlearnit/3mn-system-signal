#!/bin/bash
# Setup VN30 Realtime Monitor

echo "🚀 Setting up VN30 Realtime Monitor..."

# Get current directory
PROJECT_DIR=$(pwd)

# Create logs directory if it doesn't exist
mkdir -p logs

# Make the script executable
chmod +x vn30_realtime_monitor.py

echo "✅ VN30 Realtime Monitor setup completed!"
echo ""
echo "📈 VN30 Realtime Monitor Features:"
echo "   🎯 Single Symbol: VN30 Index (VN-Index)"
echo "   📊 SMA + MACD: Hybrid signal analysis using YAML config"
echo "   ⏰ 3-Timeframe Analysis: 1m, 2m, 5m (realtime + historical)"
echo "   🎯 Market Hours: Only runs when VN market is open (09:00-15:00 UTC+7, Mon-Fri)"
echo "   📈 Confidence Scoring: Signal reliability"
echo "   🔄 Realtime Processing: Combines realtime data with historical data"
echo "   📁 YAML Config: Uses config/symbols/VN30.yaml instead of DB thresholds"
echo ""
echo "🚀 To run manually:"
echo "   python vn30_realtime_monitor.py"
echo ""
echo "🚀 To run in Docker:"
echo "   docker-compose exec market_monitor python vn30_realtime_monitor.py"
echo ""
echo "📊 Configuration Files:"
echo "   - config/symbols/VN30.yaml (VN30 specific thresholds)"
echo "   - config/vn_market.yaml (VN market configuration)"
echo ""
echo "📈 Signal Types:"
echo "   - STRONG_BUY: Both SMA and MACD bullish"
echo "   - BUY: One bullish, one neutral"
echo "   - WEAK_BUY: SMA bullish, MACD bearish (conflict)"
echo "   - NEUTRAL: Both neutral"
echo "   - WEAK_SELL: SMA bearish, MACD bullish (conflict)"
echo "   - SELL: One bearish, one neutral"
echo "   - STRONG_SELL: Both SMA and MACD bearish"
echo ""
echo "⚠️ Note: Ensure your database has historical data for VN30 Index."
