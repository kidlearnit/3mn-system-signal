#!/bin/bash

# 🔧 3MN Trading Signals - Deployment Troubleshooting Script
# This script helps diagnose and fix common deployment issues

set -e  # Exit on any error

echo "🔧 3MN Trading Signals - Deployment Troubleshooting"
echo "================================================="

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

print_fix() {
    echo -e "${PURPLE}[FIX]${NC} $1"
}

# Check Docker status
check_docker() {
    print_status "Checking Docker status..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        print_fix "Please install Docker: https://docs.docker.com/get-docker/"
        return 1
    fi
    
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running"
        print_fix "Please start Docker Desktop or Docker daemon"
        return 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        print_fix "Please install Docker Compose: https://docs.docker.com/compose/install/"
        return 1
    fi
    
    print_success "Docker and Docker Compose are working"
}

# Check port availability
check_ports() {
    print_status "Checking port availability..."
    
    ports=(3309 6379 5010)
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            print_warning "Port $port is already in use"
            print_fix "Free the port or change configuration in docker-compose.yml"
        else
            print_success "Port $port is available"
        fi
    done
}

# Check environment file
check_environment() {
    print_status "Checking environment configuration..."
    
    if [ ! -f .env ]; then
        print_error ".env file not found"
        print_fix "Create .env file from env.example: cp env.example .env"
        return 1
    fi
    
    # Check required variables
    required_vars=("DATABASE_URL" "REDIS_URL" "MYSQL_ROOT_PASSWORD" "MYSQL_PASSWORD")
    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" .env; then
            print_error "Required environment variable $var not found"
            print_fix "Add $var to .env file"
        else
            print_success "Environment variable $var is set"
        fi
    done
}

# Check Docker services
check_services() {
    print_status "Checking Docker services..."
    
    if [ ! -f docker-compose.yml ]; then
        print_error "docker-compose.yml not found"
        print_fix "Ensure you're in the project root directory"
        return 1
    fi
    
    # Check if services are running
    if ! docker-compose ps | grep -q "running"; then
        print_warning "No services are running"
        print_fix "Start services: docker-compose up -d"
        return 1
    fi
    
    # Check each service
    services=("mysql" "redis" "web" "worker" "scheduler")
    for service in "${services[@]}"; do
        if docker-compose ps | grep -q "$service.*running"; then
            print_success "Service $service is running"
        else
            print_error "Service $service is not running"
            print_fix "Check logs: docker-compose logs $service"
        fi
    done
}

# Check database connectivity
check_database_connectivity() {
    print_status "Checking database connectivity..."
    
    # Check MySQL container
    if ! docker-compose exec -T mysql mysqladmin ping -h localhost --silent; then
        print_error "MySQL container is not responding"
        print_fix "Restart MySQL: docker-compose restart mysql"
        return 1
    fi
    
    # Check database connection from worker
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
        print_error "Database connection from worker failed"
        print_fix "Check DATABASE_URL in .env file"
        return 1
    fi
    
    print_success "Database connectivity is working"
}

# Check Redis connectivity
check_redis_connectivity() {
    print_status "Checking Redis connectivity..."
    
    if ! docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        print_error "Redis container is not responding"
        print_fix "Restart Redis: docker-compose restart redis"
        return 1
    fi
    
    print_success "Redis connectivity is working"
}

# Check web interface
check_web_interface() {
    print_status "Checking web interface..."
    
    if ! curl -s http://localhost:5010/ > /dev/null; then
        print_error "Web interface is not accessible"
        print_fix "Check web service logs: docker-compose logs web"
        return 1
    fi
    
    print_success "Web interface is accessible"
}

# Check logs for errors
check_logs() {
    print_status "Checking logs for errors..."
    
    services=("mysql" "redis" "web" "worker" "scheduler")
    for service in "${services[@]}"; do
        print_status "Checking $service logs..."
        
        # Get recent error logs
        errors=$(docker-compose logs --tail=50 $service 2>&1 | grep -i "error\|exception\|failed" | head -5)
        
        if [ -n "$errors" ]; then
            print_warning "Found errors in $service logs:"
            echo "$errors"
            print_fix "Check full logs: docker-compose logs $service"
        else
            print_success "No recent errors in $service logs"
        fi
    done
}

# Check disk space
check_disk_space() {
    print_status "Checking disk space..."
    
    # Check available disk space
    available=$(df -h . | awk 'NR==2 {print $4}')
    print_status "Available disk space: $available"
    
    # Check Docker disk usage
    docker_usage=$(docker system df --format "table {{.Type}}\t{{.TotalCount}}\t{{.Size}}" 2>/dev/null | tail -n +2)
    if [ -n "$docker_usage" ]; then
        print_status "Docker disk usage:"
        echo "$docker_usage"
    fi
    
    # Check if disk space is low
    available_bytes=$(df . | awk 'NR==2 {print $4}')
    if [ $available_bytes -lt 1073741824 ]; then  # Less than 1GB
        print_warning "Low disk space detected"
        print_fix "Free up disk space or clean Docker: docker system prune"
    else
        print_success "Sufficient disk space available"
    fi
}

# Check memory usage
check_memory() {
    print_status "Checking memory usage..."
    
    # Check system memory
    if command -v free &> /dev/null; then
        memory_info=$(free -h | grep "Mem:")
        print_status "System memory: $memory_info"
    fi
    
    # Check Docker memory usage
    docker_stats=$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | tail -n +2)
    if [ -n "$docker_stats" ]; then
        print_status "Docker container memory usage:"
        echo "$docker_stats"
    fi
}

# Fix common issues
fix_common_issues() {
    print_status "Attempting to fix common issues..."
    
    # Restart services if they're not running properly
    if ! docker-compose ps | grep -q "running"; then
        print_fix "Restarting all services..."
        docker-compose down
        docker-compose up -d
        sleep 10
    fi
    
    # Clean up Docker if disk space is low
    if [ $(df . | awk 'NR==2 {print $4}') -lt 1073741824 ]; then
        print_fix "Cleaning up Docker to free space..."
        docker system prune -f
    fi
    
    # Reset database if connection fails
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
        print_fix "Resetting database..."
        docker-compose restart mysql
        sleep 15
        docker-compose exec -T worker python scripts/auto_setup_db.py
    fi
}

# Generate diagnostic report
generate_diagnostic_report() {
    print_status "Generating diagnostic report..."
    
    REPORT_FILE="diagnostic_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "🔧 3MN Trading Signals - Diagnostic Report"
        echo "Generated: $(date)"
        echo "=========================================="
        echo ""
        
        echo "📊 System Information:"
        echo "OS: $(uname -a)"
        echo "Docker Version: $(docker --version)"
        echo "Docker Compose Version: $(docker-compose --version)"
        echo ""
        
        echo "📊 Services Status:"
        docker-compose ps
        echo ""
        
        echo "📊 Disk Space:"
        df -h
        echo ""
        
        echo "📊 Memory Usage:"
        if command -v free &> /dev/null; then
            free -h
        fi
        echo ""
        
        echo "📊 Docker System Info:"
        docker system df
        echo ""
        
        echo "📊 Recent Logs (last 20 lines per service):"
        services=("mysql" "redis" "web" "worker" "scheduler")
        for service in "${services[@]}"; do
            echo "--- $service ---"
            docker-compose logs --tail=20 $service
            echo ""
        done
        
    } > "$REPORT_FILE"
    
    print_success "Diagnostic report generated: $REPORT_FILE"
}

# Interactive troubleshooting menu
interactive_menu() {
    while true; do
        echo ""
        echo "🔧 Troubleshooting Menu:"
        echo "1. Check Docker status"
        echo "2. Check port availability"
        echo "3. Check environment configuration"
        echo "4. Check services"
        echo "5. Check database connectivity"
        echo "6. Check Redis connectivity"
        echo "7. Check web interface"
        echo "8. Check logs for errors"
        echo "9. Check disk space"
        echo "10. Check memory usage"
        echo "11. Fix common issues"
        echo "12. Generate diagnostic report"
        echo "13. Run all checks"
        echo "0. Exit"
        echo ""
        read -p "Select option (0-13): " choice
        
        case $choice in
            1) check_docker ;;
            2) check_ports ;;
            3) check_environment ;;
            4) check_services ;;
            5) check_database_connectivity ;;
            6) check_redis_connectivity ;;
            7) check_web_interface ;;
            8) check_logs ;;
            9) check_disk_space ;;
            10) check_memory ;;
            11) fix_common_issues ;;
            12) generate_diagnostic_report ;;
            13) 
                check_docker
                check_ports
                check_environment
                check_services
                check_database_connectivity
                check_redis_connectivity
                check_web_interface
                check_logs
                check_disk_space
                check_memory
                ;;
            0) 
                print_success "Troubleshooting completed"
                exit 0
                ;;
            *) 
                print_error "Invalid option. Please select 0-13."
                ;;
        esac
    done
}

# Main function
main() {
    if [ "$1" = "--interactive" ] || [ "$1" = "-i" ]; then
        interactive_menu
    else
        # Run all checks automatically
        check_docker
        check_ports
        check_environment
        check_services
        check_database_connectivity
        check_redis_connectivity
        check_web_interface
        check_logs
        check_disk_space
        check_memory
        generate_diagnostic_report
        
        echo ""
        print_success "🔧 Troubleshooting completed!"
        print_status "Use --interactive flag for interactive menu: ./troubleshoot_deployment.sh --interactive"
    fi
}

# Run main function
main "$@"
