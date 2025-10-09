#!/bin/bash

# Script kiểm tra health của trading system
echo "🔍 3MN Trading Signals - System Health Check"
echo "============================================="

# Kiểm tra Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not installed"
    exit 1
fi

echo "✅ Docker and Docker Compose available"

# Kiểm tra .env file
if [ ! -f .env ]; then
    echo "❌ .env file not found"
    exit 1
fi

echo "✅ .env file found"

# Kiểm tra containers đang chạy
echo ""
echo "📊 Container Status:"
echo "==================="

if docker-compose ps | grep -q "Up"; then
    docker-compose ps
else
    echo "❌ No containers running"
    echo "💡 Run ./start.sh to start the system"
    exit 1
fi

echo ""
echo "🔍 Service Health Check:"
echo "======================="

# Kiểm tra MySQL
echo -n "MySQL: "
if docker-compose exec mysql mysqladmin ping -h localhost --silent 2>/dev/null; then
    echo "✅ Healthy"
    
    # Kiểm tra database
    if docker-compose exec mysql mysql -u trader -ptraderpass -e "USE trading; SHOW TABLES;" 2>/dev/null | grep -q "symbols"; then
        echo "  📊 Database: ✅ Ready"
        
        # Đếm symbols
        SYMBOL_COUNT=$(docker-compose exec mysql mysql -u trader -ptraderpass -e "USE trading; SELECT COUNT(*) FROM symbols;" 2>/dev/null | tail -1)
        echo "  📈 Symbols: $SYMBOL_COUNT"
    else
        echo "  📊 Database: ❌ Not initialized"
    fi
else
    echo "❌ Not responding"
fi

# Kiểm tra Redis
echo -n "Redis: "
if docker-compose exec redis redis-cli ping 2>/dev/null | grep -q PONG; then
    echo "✅ Healthy"
    
    # Kiểm tra queues
    QUEUE_COUNT=$(docker-compose exec redis redis-cli LLEN vn 2>/dev/null || echo "0")
    echo "  🔄 VN Queue: $QUEUE_COUNT jobs"
    
    QUEUE_COUNT=$(docker-compose exec redis redis-cli LLEN us 2>/dev/null || echo "0")
    echo "  🔄 US Queue: $QUEUE_COUNT jobs"
    
    QUEUE_COUNT=$(docker-compose exec redis redis-cli LLEN backfill 2>/dev/null || echo "0")
    echo "  🔄 Backfill Queue: $QUEUE_COUNT jobs"
else
    echo "❌ Not responding"
fi

# Kiểm tra Web service
echo -n "Web: "
if curl -s http://localhost:5010 > /dev/null 2>&1; then
    echo "✅ Healthy (http://localhost:5010)"
else
    echo "❌ Not responding"
fi

# Kiểm tra Workers
echo ""
echo "👷 Worker Status:"
echo "================="

WORKERS=("worker_vn" "worker_us" "worker_backfill" "scheduler")

for worker in "${WORKERS[@]}"; do
    if docker-compose ps $worker | grep -q "Up"; then
        echo "✅ $worker: Running"
    else
        echo "❌ $worker: Stopped"
    fi
done

# Kiểm tra recent logs
echo ""
echo "📝 Recent Activity:"
echo "=================="

# Lấy logs gần nhất từ scheduler
echo "Scheduler (last 5 lines):"
docker-compose logs --tail=5 scheduler 2>/dev/null | grep -v "DEBUG" || echo "  No recent activity"

# Lấy logs gần nhất từ worker_us
echo ""
echo "Worker US (last 3 lines):"
docker-compose logs --tail=3 worker_us 2>/dev/null | grep -E "(Starting|Finished|Job OK)" || echo "  No recent activity"

echo ""
echo "💡 Quick Commands:"
echo "  ./quick check <SYMBOL>    - Check symbol data"
echo "  ./quick list             - List all symbols"
echo "  ./quick stats            - System statistics"
echo "  docker-compose logs -f   - Follow all logs"
echo "  ./stop.sh               - Stop system"
