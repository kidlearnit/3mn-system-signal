#!/bin/bash

# Start Backend Services
echo "🚀 Starting Backend Services..."
echo "==============================="

# Check if .env file exists
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

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Remove old volumes if fresh start requested
if [ "$1" = "--fresh" ]; then
    echo "🗑️ Removing old volumes (fresh start)..."
    docker-compose down -v
    docker volume prune -f
fi

# Build and start services
echo "🔨 Building and starting backend services..."
docker-compose up --build -d

# Wait for database setup
echo "⏳ Waiting for database setup..."
docker-compose logs -f db_setup

# Check services status
echo "🔍 Checking services status..."
docker-compose ps

# Display system status
echo "📊 Backend System Status:"
echo "========================="

# Check MySQL
if docker-compose exec mysql mysqladmin ping -h localhost --silent; then
    echo "✅ MySQL: Running"
else
    echo "❌ MySQL: Not responding"
fi

# Check Redis
if docker-compose exec redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis: Running"
else
    echo "❌ Redis: Not responding"
fi

# Check Web service
if curl -s http://localhost:5010 > /dev/null; then
    echo "✅ Web API: Running (http://localhost:5010)"
else
    echo "❌ Web API: Not responding"
fi

# Display workers
echo "👷 Workers status:"
docker-compose ps | grep worker

echo ""
echo "🎉 Backend services started successfully!"
echo ""
echo "📋 Available endpoints:"
echo "  API: http://localhost:5010"
echo "  API Docs: http://localhost:5010/docs"
echo "  Health: http://localhost:5010/api/system/health"
echo ""
echo "🗄️ Database: localhost:3309 (user: trader, pass: traderpass)"
echo "🔄 Redis: localhost:6379"
echo ""
echo "📝 To view logs: docker-compose logs -f [service_name]"
echo "🛑 To stop: docker-compose down"
echo "🔄 To restart: docker-compose restart [service_name]"
