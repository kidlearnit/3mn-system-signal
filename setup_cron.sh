#!/bin/bash
# Setup cron jobs for market monitoring

echo "🐳 Setting up cron jobs for market monitoring..."

# Get current directory
PROJECT_DIR=$(pwd)
COMPOSE_FILE="docker-compose.market-monitor.yml"

echo "📁 Project directory: $PROJECT_DIR"
echo "📋 Compose file: $COMPOSE_FILE"

# Check if compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ Error: $COMPOSE_FILE not found!"
    exit 1
fi

# Create cron entries
CRON_ENTRIES="
# Market Signal Monitor - VN Market
# VN Market - Morning session (9:05, 9:35, 10:05, 10:35, 11:05)
5,35 9 * * 1-5 cd $PROJECT_DIR && docker-compose -f $COMPOSE_FILE run --rm market-monitor python run_market_monitor.py --mode single --market VN
5,35 10 * * 1-5 cd $PROJECT_DIR && docker-compose -f $COMPOSE_FILE run --rm market-monitor python run_market_monitor.py --mode single --market VN
5 11 * * 1-5 cd $PROJECT_DIR && docker-compose -f $COMPOSE_FILE run --rm market-monitor python run_market_monitor.py --mode single --market VN

# VN Market - Afternoon session (13:05, 13:35, 14:05, 14:35)
5,35 13 * * 1-5 cd $PROJECT_DIR && docker-compose -f $COMPOSE_FILE run --rm market-monitor python run_market_monitor.py --mode single --market VN
5,35 14 * * 1-5 cd $PROJECT_DIR && docker-compose -f $COMPOSE_FILE run --rm market-monitor python run_market_monitor.py --mode single --market VN

# Market Signal Monitor - US Market
# US Market - Trading hours (9:35, 10:05, 10:35, 11:05, 11:35, 12:05, 12:35, 13:05, 13:35, 14:05, 14:35, 15:05)
35 9 * * 1-5 cd $PROJECT_DIR && docker-compose -f $COMPOSE_FILE run --rm market-monitor python run_market_monitor.py --mode single --market US
5,35 10 * * 1-5 cd $PROJECT_DIR && docker-compose -f $COMPOSE_FILE run --rm market-monitor python run_market_monitor.py --mode single --market US
5,35 11 * * 1-5 cd $PROJECT_DIR && docker-compose -f $COMPOSE_FILE run --rm market-monitor python run_market_monitor.py --mode single --market US
5,35 12 * * 1-5 cd $PROJECT_DIR && docker-compose -f $COMPOSE_FILE run --rm market-monitor python run_market_monitor.py --mode single --market US
5,35 13 * * 1-5 cd $PROJECT_DIR && docker-compose -f $COMPOSE_FILE run --rm market-monitor python run_market_monitor.py --mode single --market US
5,35 14 * * 1-5 cd $PROJECT_DIR && docker-compose -f $COMPOSE_FILE run --rm market-monitor python run_market_monitor.py --mode single --market US
5 15 * * 1-5 cd $PROJECT_DIR && docker-compose -f $COMPOSE_FILE run --rm market-monitor python run_market_monitor.py --mode single --market US
"

echo "📅 Adding cron jobs..."

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_ENTRIES") | crontab -

if [ $? -eq 0 ]; then
    echo "✅ Cron jobs setup completed successfully!"
    echo ""
    echo "📋 Current cron jobs:"
    crontab -l | grep -E "(Market Signal Monitor|docker-compose)"
    echo ""
    echo "🔍 To view all cron jobs: crontab -l"
    echo "🗑️  To remove all cron jobs: crontab -r"
    echo ""
    echo "🧪 To test a job manually:"
    echo "   docker-compose -f $COMPOSE_FILE run --rm market-monitor python run_market_monitor.py --mode single --market VN"
else
    echo "❌ Error setting up cron jobs!"
    exit 1
fi
