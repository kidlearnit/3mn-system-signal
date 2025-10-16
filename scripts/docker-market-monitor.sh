#!/bin/bash

# Script để quản lý Market Signal Monitor với Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.market-monitor.yml"
ENV_FILE=".env.market-monitor"
CONTAINER_NAME="market-signal-monitor"

# Functions
print_header() {
    echo -e "${BLUE}🚀 Market Signal Monitor Docker Manager${NC}"
    echo "=================================="
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_requirements() {
    print_info "Checking requirements..."
    
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
    
    # Check environment file
    if [ ! -f "$ENV_FILE" ]; then
        print_warning "Environment file $ENV_FILE not found."
        print_info "Creating from example..."
        if [ -f "env.market-monitor.example" ]; then
            cp env.market-monitor.example "$ENV_FILE"
            print_success "Environment file created. Please edit $ENV_FILE with your configuration."
        else
            print_error "Example environment file not found."
            exit 1
        fi
    fi
    
    print_success "Requirements check passed"
}

build_image() {
    print_info "Building Market Signal Monitor image..."
    docker-compose -f "$COMPOSE_FILE" build
    print_success "Image built successfully"
}

start_monitor() {
    print_info "Starting Market Signal Monitor..."
    
    # Check if container is already running
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        print_warning "Container is already running"
        return 0
    fi
    
    # Start the service
    docker-compose -f "$COMPOSE_FILE" up -d
    
    # Wait for container to be ready
    print_info "Waiting for container to be ready..."
    sleep 10
    
    # Check container status
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        print_success "Market Signal Monitor started successfully"
        print_info "Container name: $CONTAINER_NAME"
    else
        print_error "Failed to start Market Signal Monitor"
        return 1
    fi
}

stop_monitor() {
    print_info "Stopping Market Signal Monitor..."
    docker-compose -f "$COMPOSE_FILE" down
    print_success "Market Signal Monitor stopped"
}

restart_monitor() {
    print_info "Restarting Market Signal Monitor..."
    stop_monitor
    sleep 5
    start_monitor
}

show_status() {
    print_info "Market Signal Monitor Status:"
    echo "================================"
    
    # Container status
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        print_success "Container is running"
        
        # Show container info
        echo ""
        print_info "Container Information:"
        docker ps -f name="$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        
        # Show logs (last 10 lines)
        echo ""
        print_info "Recent Logs:"
        docker logs --tail 10 "$CONTAINER_NAME"
        
    else
        print_warning "Container is not running"
    fi
    
    # Show health status
    echo ""
    print_info "Health Status:"
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "unknown")
        case $HEALTH_STATUS in
            "healthy")
                print_success "Container is healthy"
                ;;
            "unhealthy")
                print_error "Container is unhealthy"
                ;;
            "starting")
                print_warning "Container is starting"
                ;;
            *)
                print_info "Health status: $HEALTH_STATUS"
                ;;
        esac
    fi
}

show_logs() {
    print_info "Showing Market Signal Monitor logs..."
    echo "Press Ctrl+C to exit"
    echo "================================"
    docker logs -f "$CONTAINER_NAME"
}

test_telegram() {
    print_info "Testing Telegram connection..."
    docker exec "$CONTAINER_NAME" python test_telegram_connection.py
}

update_monitor() {
    print_info "Updating Market Signal Monitor..."
    
    # Pull latest changes (if using git)
    if [ -d ".git" ]; then
        print_info "Pulling latest changes..."
        git pull
    fi
    
    # Rebuild and restart
    build_image
    restart_monitor
    
    print_success "Market Signal Monitor updated successfully"
}

show_help() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start Market Signal Monitor"
    echo "  stop      Stop Market Signal Monitor"
    echo "  restart   Restart Market Signal Monitor"
    echo "  status    Show status and logs"
    echo "  logs      Show live logs"
    echo "  build     Build Docker image"
    echo "  test      Test Telegram connection"
    echo "  update    Update and restart monitor"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 status"
    echo "  $0 logs"
}

# Main script
main() {
    print_header
    
    case "${1:-help}" in
        start)
            check_requirements
            start_monitor
            ;;
        stop)
            stop_monitor
            ;;
        restart)
            check_requirements
            restart_monitor
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        build)
            check_requirements
            build_image
            ;;
        test)
            test_telegram
            ;;
        update)
            check_requirements
            update_monitor
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
