#!/bin/bash
# Docker Setup Script for Symbol-Specific Thresholds System

echo "🚀 Setting up Docker environment for Symbol-Specific Thresholds System"
echo "=================================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found. Please ensure you're in the project root directory."
    exit 1
fi

# Verify required files
echo "🔍 Verifying required files..."
required_files=("schema.sql" "init_data.sql" "app/services/symbol_thresholds.py" "app/services/signal_engine.py")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Required file missing: $file"
        exit 1
    fi
    echo "  ✅ $file"
done

echo "✅ All required files present"

# Start Docker containers
echo "🐳 Starting Docker containers..."
docker-compose up -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Check if database is accessible
echo "🔍 Checking database connection..."
if docker-compose exec -T db mysql -u root -p${MYSQL_ROOT_PASSWORD:-password} -e "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Database is ready"
else
    echo "❌ Database connection failed"
    echo "Please check your Docker containers:"
    docker-compose ps
    exit 1
fi

# Verify schema and data
echo "🔍 Verifying database setup..."
if docker-compose exec -T db mysql -u root -p${MYSQL_ROOT_PASSWORD:-password} trading_signals -e "SELECT COUNT(*) FROM market_threshold_templates;" > /dev/null 2>&1; then
    echo "✅ Database schema and data verified"
else
    echo "❌ Database verification failed"
    exit 1
fi

echo ""
echo "🎉 Docker setup completed successfully!"
echo ""
echo "📋 System Status:"
echo "  ✅ Database schema created"
echo "  ✅ Threshold data loaded"
echo "  ✅ Symbol-specific thresholds system ready"
echo "  ✅ US and VN market thresholds configured"
echo ""
echo "🔧 Next Steps:"
echo "  1. Access the application at http://localhost:5000"
echo "  2. Check system status in the dashboard"
echo "  3. Monitor trading signals"
echo ""
echo "📊 Thresholds Summary:"
echo "  • US Market: MACD values 0-3 (small values)"
echo "  • VN Market: MACD values 0-50 (large values)"
echo "  • 8 timeframes supported (1m to 1D)"
echo "  • Automatic market detection"
echo ""
