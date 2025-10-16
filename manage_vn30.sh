#!/bin/bash
# VN30 Service Management Script

PROJECT_DIR=$(pwd)
COMPOSE_FILE="docker-compose.vn30.yml"

echo "🚀 VN30 Service Management"
echo "=========================="

case "$1" in
    "start")
        echo "🚀 Starting VN30 services..."
        docker-compose -f $COMPOSE_FILE up -d
        echo "✅ VN30 services started"
        ;;
    "stop")
        echo "🛑 Stopping VN30 services..."
        docker-compose -f $COMPOSE_FILE down
        echo "✅ VN30 services stopped"
        ;;
    "restart")
        echo "🔄 Restarting VN30 services..."
        docker-compose -f $COMPOSE_FILE down
        docker-compose -f $COMPOSE_FILE up -d
        echo "✅ VN30 services restarted"
        ;;
    "logs")
        echo "📊 VN30 Monitor logs:"
        docker-compose -f $COMPOSE_FILE logs vn30_monitor --tail=20 -f
        ;;
    "status")
        echo "📊 VN30 services status:"
        docker-compose -f $COMPOSE_FILE ps
        ;;
    "backfill")
        echo "📊 Running VN30 backfill..."
        docker-compose -f $COMPOSE_FILE up vn30_backfill
        ;;
    "test")
        echo "🧪 Testing VN30 monitor..."
        docker-compose -f $COMPOSE_FILE exec vn30_monitor python -c "
import asyncio
from vn30_realtime_monitor import VN30RealtimeMonitor
monitor = VN30RealtimeMonitor()
print('✅ VN30 Monitor initialized')
print(f'📊 Market open: {monitor.is_market_open()}')
print(f'📈 Realtime data: {monitor.get_realtime_data()}')
"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|status|backfill|test}"
        echo ""
        echo "Commands:"
        echo "  start    - Start VN30 services"
        echo "  stop     - Stop VN30 services"
        echo "  restart  - Restart VN30 services"
        echo "  logs     - Show VN30 monitor logs"
        echo "  status   - Show VN30 services status"
        echo "  backfill - Run VN30 data backfill"
        echo "  test     - Test VN30 monitor functionality"
        exit 1
        ;;
esac
