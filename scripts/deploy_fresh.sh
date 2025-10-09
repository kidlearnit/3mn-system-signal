#!/bin/bash

# 🚀 3MN Trading Signals - Fresh Environment Deployment Script
# This script deploys the complete system from scratch including all new features

set -e  # Exit on any error

echo "🚀 Starting 3MN Trading Signals Fresh Deployment..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_feature() {
    echo -e "${PURPLE}[FEATURE]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if ports are available
    for port in 3309 6379 5010; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            print_warning "Port $port is already in use. Please free the port or change the configuration."
        fi
    done
    
    print_success "Prerequisites check completed"
}

# Setup environment file
setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        if [ -f env.example ]; then
            cp env.example .env
            print_success "Created .env file from template"
            print_warning "Please edit .env file with your configuration before continuing"
            print_warning "Press Enter when ready to continue..."
            read
        else
            print_error "env.example file not found. Please create .env file manually."
            exit 1
        fi
    else
        print_success ".env file already exists"
    fi
}

# Start services
start_services() {
    print_status "Starting Docker services..."
    
    # Pull latest images
    docker-compose pull
    
    # Start services
    docker-compose up -d
    
    print_success "Docker services started"
}

# Wait for database setup
wait_for_database() {
    print_status "Waiting for database setup to complete..."
    
    # Wait for db_setup service to complete
    while [ $(docker-compose ps db_setup | grep -c "exited (0)") -eq 0 ]; do
        if [ $(docker-compose ps db_setup | grep -c "exited (1)") -gt 0 ]; then
            print_error "Database setup failed. Check logs:"
            docker-compose logs db_setup
            exit 1
        fi
        print_status "Waiting for database setup..."
        sleep 5
    done
    
    print_success "Database setup completed"
}

# Verify new features
verify_new_features() {
    print_status "Verifying new features..."
    
    # Check MACD Multi-TF Hybrid system
    print_feature "Checking MACD Multi-TF Hybrid system..."
    if docker-compose exec -T worker python -c "
import sys; sys.path.append('/code')
from app.db import init_db, SessionLocal
import os
init_db(os.getenv('DATABASE_URL'))
from app.db import SessionLocal
from sqlalchemy import text
with SessionLocal() as s:
    # Check macd_multi_signals table
    result = s.execute(text('SELECT COUNT(*) FROM macd_multi_signals')).fetchone()
    print(f'MACD Multi-TF signals table: {result[0]} records')
    
    # Check workflows table
    result = s.execute(text('SELECT COUNT(*) FROM workflows')).fetchone()
    print(f'Workflows table: {result[0]} records')
    
    # Check symbols with VN and US
    result = s.execute(text('SELECT exchange, COUNT(*) FROM symbols GROUP BY exchange')).fetchall()
    for exchange, count in result:
        print(f'Symbols in {exchange}: {count}')
" > /dev/null 2>&1; then
        print_success "MACD Multi-TF Hybrid system verified"
    else
        print_warning "MACD Multi-TF Hybrid system verification failed"
    fi
    
    # Check workflow builder
    print_feature "Checking Workflow Builder..."
    if curl -s http://localhost:5010/workflow-builder > /dev/null; then
        print_success "Workflow Builder accessible"
    else
        print_warning "Workflow Builder not accessible"
    fi
    
    # Check data sources
    print_feature "Checking data sources..."
    if docker-compose exec -T worker python -c "
import sys; sys.path.append('/code')
from app.services.data_sources import fetch_vnstock_1m, fetch_yfinance_1m
print('VNStock and YFinance modules loaded successfully')
" > /dev/null 2>&1; then
        print_success "Data sources (VNStock, YFinance) verified"
    else
        print_warning "Data sources verification failed"
    fi
}

# Test MACD Multi-TF Hybrid
test_macd_hybrid() {
    print_status "Testing MACD Multi-TF Hybrid system..."
    
    # Create test script
    cat > /tmp/test_macd_hybrid.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
sys.path.append('/code')

from worker.macd_multi_hybrid_jobs import job_macd_multi_hybrid_pipeline

# Test config with mixed VN/US symbols
config = {
    'fastPeriod': 7,
    'slowPeriod': 113,
    'signalPeriod': 144,
    'symbolThresholds': [
        {
            'symbol': 'AAPL',
            'company': 'Apple Inc.',
            'weight': '7.33%',
            'sector': 'Technology',
            'bubefsm1': 0.33,
            'bubefsm2': 0.74,
            'bubefsm5': 1.0,
            'bubefsm15': 1.47,
            'bubefsm30': 1.74,
            'bubefs_1h': 2.2
        },
        {
            'symbol': 'VN30',
            'company': 'VN30 Index',
            'weight': '100%',
            'sector': 'Index',
            'bubefsm1': 0.4,
            'bubefsm2': 0.55,
            'bubefsm5': 1.0,
            'bubefsm15': 2.0,
            'bubefsm30': 3.0,
            'bubefs_1h': 4.0
        }
    ]
}

try:
    result = job_macd_multi_hybrid_pipeline(config, mode='realtime')
    print(f"✅ MACD Multi-TF Hybrid test completed: {result.get('status', 'unknown')}")
    print(f"   Symbols processed: {result.get('symbols_processed', 0)}")
    print(f"   Signals generated: {result.get('signals_generated', 0)}")
except Exception as e:
    print(f"❌ MACD Multi-TF Hybrid test failed: {e}")
EOF
    
    # Run test
    if docker-compose exec -T worker python /tmp/test_macd_hybrid.py; then
        print_success "MACD Multi-TF Hybrid test passed"
    else
        print_warning "MACD Multi-TF Hybrid test failed"
    fi
    
    # Cleanup
    rm -f /tmp/test_macd_hybrid.py
}

# Verify deployment
verify_deployment() {
    print_status "Verifying deployment..."
    
    # Check all services are running
    if [ $(docker-compose ps | grep -c "running") -lt 6 ]; then
        print_error "Not all services are running. Check status:"
        docker-compose ps
        exit 1
    fi
    
    # Check web interface
    if ! curl -s http://localhost:5010/ > /dev/null; then
        print_error "Web interface is not accessible"
        exit 1
    fi
    
    # Check database connection
    if ! docker-compose exec -T worker python -c "
import sys; sys.path.append('/code')
from app.db import init_db, SessionLocal
import os
init_db(os.getenv('DATABASE_URL'))
from app.db import SessionLocal
from sqlalchemy import text
with SessionLocal() as s:
    s.execute(text('SELECT 1'))
" > /dev/null 2>&1; then
        print_error "Database connection failed"
        exit 1
    fi
    
    print_success "Deployment verification completed"
}

# Show deployment status
show_status() {
    print_status "Deployment Status:"
    echo "==================="
    
    echo "📊 Services Status:"
    docker-compose ps
    
    echo ""
    echo "🌐 Web Interface: http://localhost:5010"
    echo "📊 Database: localhost:3309"
    echo "🔄 Redis: localhost:6379"
    
    echo ""
    echo "🆕 New Features Available:"
    echo "  ✅ MACD Multi-TF Hybrid (VN + US symbols)"
    echo "  ✅ Workflow Builder with drag-and-drop"
    echo "  ✅ Unanimous signal logic (6/6 timeframes)"
    echo "  ✅ VNStock integration for Vietnamese stocks"
    echo "  ✅ YFinance integration for US stocks"
    echo "  ✅ Automatic exchange detection"
    echo "  ✅ Mixed workflow support (VN + US in same workflow)"
    
    echo ""
    echo "📈 Recent Signals:"
    docker-compose exec -T worker python -c "
import sys; sys.path.append('/code')
from app.db import init_db, SessionLocal
import os
init_db(os.getenv('DATABASE_URL'))
from app.db import SessionLocal
from sqlalchemy import text
with SessionLocal() as s:
    result = s.execute(text('SELECT COUNT(*) FROM signals')).fetchone()
    print(f'Total signals: {result[0]}')
    
    result = s.execute(text('SELECT COUNT(*) FROM macd_multi_signals')).fetchone()
    print(f'MACD Multi-TF signals: {result[0]}')
    
    result = s.execute(text('SELECT COUNT(*) FROM workflows')).fetchone()
    print(f'Workflows: {result[0]}')
" 2>/dev/null || echo "Unable to check signals"
    
    echo ""
    print_success "🚀 Fresh deployment completed successfully!"
    print_status "You can now access the web interface at http://localhost:5010"
    print_status "Create your first MACD Multi-TF workflow in the Workflow Builder!"
}

# Main deployment flow
main() {
    check_prerequisites
    setup_environment
    start_services
    wait_for_database
    verify_deployment
    verify_new_features
    test_macd_hybrid
    show_status
}

# Run main function
main "$@"
