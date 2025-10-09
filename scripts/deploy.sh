#!/bin/bash

# 🚀 3MN Trading Signals - Deployment Script
# This script automates the deployment process for a fresh environment

set -e  # Exit on any error

echo "🚀 Starting 3MN Trading Signals Deployment..."
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
" 2>/dev/null || echo "Unable to check signals"
    
    echo ""
    print_success "🚀 Deployment completed successfully!"
    print_status "You can now access the web interface at http://localhost:5010"
}

# Main deployment flow
main() {
    check_prerequisites
    setup_environment
    start_services
    wait_for_database
    verify_deployment
    show_status
}

# Run main function
main "$@"
