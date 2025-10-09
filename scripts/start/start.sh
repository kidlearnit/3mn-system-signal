#!/bin/bash

# Script khởi động trading system với auto-setup (DEPRECATED - Use start-backend.sh)
echo "⚠️  DEPRECATED: This script is deprecated!"
echo "💡 Please use: ./start-backend.sh"
echo ""
echo "🚀 Starting 3MN Trading Signals System..."
echo "================================================"

# Kiểm tra .env file
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "💡 Please create .env file with required variables:"
    echo "   MYSQL_DB=trading"
    echo "   MYSQL_ROOT_PASSWORD=rootpass"
    echo "   MYSQL_USER=trader"
    echo "   MYSQL_PASSWORD=traderpass"
    echo "   DATABASE_URL=mysql+pymysql://trader:traderpass@mysql:3306/trading"
    echo "   REDIS_URL=redis://redis:6379/0"
    echo "   POLYGON_API_KEY=your_api_key"
    echo "   TG_TOKEN=your_telegram_token"
    echo "   TG_CHAT_ID=your_chat_id"
    echo "   VNSTOCK_ENABLED=true"
    echo "   YF_ENABLED=true"
    exit 1
fi

echo "✅ .env file found"

# Dừng các containers cũ (nếu có)
echo "🛑 Stopping existing containers..."
docker-compose down

# Xóa volumes cũ (nếu muốn fresh start)
if [ "$1" = "--fresh" ]; then
    echo "🗑️ Removing old volumes (fresh start)..."
    docker-compose down -v
    docker volume prune -f
fi

# Build và khởi động services
echo "🔨 Building and starting services..."
docker-compose up --build -d

# Đợi database setup hoàn thành
echo "⏳ Waiting for database setup..."
docker-compose logs -f db_setup

# Kiểm tra trạng thái services
echo "🔍 Checking services status..."
docker-compose ps

# Hiển thị logs của các services chính
echo "📊 System status:"
echo "=================="

# Kiểm tra MySQL
if docker-compose exec mysql mysqladmin ping -h localhost --silent; then
    echo "✅ MySQL: Running"
else
    echo "❌ MySQL: Not responding"
fi

# Kiểm tra Redis
if docker-compose exec redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis: Running"
else
    echo "❌ Redis: Not responding"
fi

# Kiểm tra Web service
if curl -s http://localhost:5010 > /dev/null; then
    echo "✅ Web: Running (http://localhost:5010)"
else
    echo "❌ Web: Not responding"
fi

# Hiển thị workers
echo "👷 Workers status:"
docker-compose ps | grep worker

echo ""
echo "🎉 Trading system started successfully!"
echo ""
echo "📋 Available commands:"
echo "  ./quick check <SYMBOL>    - Check symbol data"
echo "  ./quick backfill <SYMBOL> - Backfill symbol data"
echo "  ./quick list             - List all symbols"
echo "  ./quick stats            - System statistics"
echo ""
echo "📊 Web interfaces:"
echo "  Backend API: http://localhost:5010"
echo "  Frontend: http://localhost:3000 (run ./start-frontend.sh)"
echo ""
echo "🗄️ MySQL: localhost:3309 (user: trader, pass: traderpass)"
echo "🔄 Redis: localhost:6379"
echo ""
echo "📝 To view logs: docker-compose logs -f [service_name]"
echo "🛑 To stop: docker-compose down"
echo "🔄 To restart: docker-compose restart [service_name]"
echo ""
echo "🎨 Frontend commands:"
echo "  ./install-frontend.sh    - Install frontend dependencies"
echo "  ./start-frontend.sh      - Start frontend dev server"
echo "  ./build-frontend.sh      - Build frontend for production"
