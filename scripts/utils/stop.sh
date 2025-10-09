#!/bin/bash

# Script dừng trading system
echo "🛑 Stopping 3MN Trading Signals System..."
echo "=========================================="

# Dừng tất cả services
docker-compose down

echo "✅ All services stopped"

# Hiển thị options
echo ""
echo "💡 Additional options:"
echo "  ./stop.sh --clean    - Stop and remove volumes (fresh start)"
echo "  ./stop.sh --logs     - Show logs before stopping"
echo ""

# Xử lý options
case "$1" in
    --clean)
        echo "🗑️ Removing volumes for fresh start..."
        docker-compose down -v
        docker volume prune -f
        echo "✅ Volumes removed"
        ;;
    --logs)
        echo "📝 Showing recent logs..."
        docker-compose logs --tail=50
        ;;
esac

echo "🎯 System stopped successfully!"
