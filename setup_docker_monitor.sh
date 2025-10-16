#!/bin/bash

# Script để setup Market Signal Monitor với Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENV_FILE=".env.market-monitor"
ENV_EXAMPLE="env.market-monitor.example"

# Functions
print_header() {
    echo -e "${BLUE}🚀 Market Signal Monitor Docker Setup${NC}"
    echo "======================================"
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
        echo "Installation guide: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        echo "Installation guide: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

setup_environment() {
    print_info "Setting up environment configuration..."
    
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "$ENV_EXAMPLE" ]; then
            cp "$ENV_EXAMPLE" "$ENV_FILE"
            print_success "Environment file created from example"
            print_warning "Please edit $ENV_FILE with your configuration"
        else
            print_error "Example environment file not found"
            exit 1
        fi
    else
        print_info "Environment file already exists"
    fi
    
    # Check if environment variables are set
    if grep -q "your_telegram_bot_token_here" "$ENV_FILE"; then
        print_warning "Please update Telegram configuration in $ENV_FILE"
        echo ""
        echo "Required configuration:"
        echo "  - TG_TOKEN: Your Telegram bot token"
        echo "  - TG_CHAT_ID: Your Telegram chat ID"
        echo "  - DATABASE_URL: Your database connection string"
        echo ""
        read -p "Press Enter to continue after updating the configuration..."
    fi
}

test_telegram_config() {
    print_info "Testing Telegram configuration..."
    
    # Load environment variables
    if [ -f "$ENV_FILE" ]; then
        export $(grep -v '^#' "$ENV_FILE" | xargs)
    fi
    
    if [ -z "$TG_TOKEN" ] || [ -z "$TG_CHAT_ID" ]; then
        print_error "Telegram configuration is missing"
        print_warning "Please set TG_TOKEN and TG_CHAT_ID in $ENV_FILE"
        return 1
    fi
    
    # Test Telegram connection
    print_info "Testing Telegram connection..."
    if python test_telegram_connection.py; then
        print_success "Telegram configuration is working"
        return 0
    else
        print_error "Telegram configuration test failed"
        return 1
    fi
}

build_docker_image() {
    print_info "Building Docker image..."
    
    if docker-compose -f docker-compose.market-monitor.yml build; then
        print_success "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
}

start_monitor() {
    print_info "Starting Market Signal Monitor..."
    
    # Start the service
    if docker-compose -f docker-compose.market-monitor.yml up -d; then
        print_success "Market Signal Monitor started successfully"
        
        # Wait for container to be ready
        print_info "Waiting for container to be ready..."
        sleep 10
        
        # Check container status
        if docker ps -q -f name="market-signal-monitor" | grep -q .; then
            print_success "Container is running"
            print_info "Container name: market-signal-monitor"
        else
            print_error "Container failed to start"
            return 1
        fi
    else
        print_error "Failed to start Market Signal Monitor"
        exit 1
    fi
}

show_status() {
    print_info "Market Signal Monitor Status:"
    echo "================================"
    
    # Container status
    if docker ps -q -f name="market-signal-monitor" | grep -q .; then
        print_success "Container is running"
        
        # Show container info
        echo ""
        print_info "Container Information:"
        docker ps -f name="market-signal-monitor" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        
        # Show logs (last 10 lines)
        echo ""
        print_info "Recent Logs:"
        docker logs --tail 10 market-signal-monitor
        
    else
        print_warning "Container is not running"
    fi
}

show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup     Complete setup (recommended for first time)"
    echo "  start     Start Market Signal Monitor"
    echo "  stop      Stop Market Signal Monitor"
    echo "  restart   Restart Market Signal Monitor"
    echo "  status    Show status and logs"
    echo "  logs      Show live logs"
    echo "  test      Test Telegram connection"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup    # First time setup"
    echo "  $0 start    # Start the monitor"
    echo "  $0 status   # Check status"
}

# Main script
main() {
    print_header
    
    case "${1:-help}" in
        setup)
            check_requirements
            setup_environment
            if test_telegram_config; then
                build_docker_image
                start_monitor
                show_status
                print_success "Setup completed successfully!"
                print_info "Market Signal Monitor is now running and will automatically monitor markets during trading hours."
            else
                print_error "Setup failed due to Telegram configuration issues"
                exit 1
            fi
            ;;
        start)
            check_requirements
            start_monitor
            show_status
            ;;
        stop)
            print_info "Stopping Market Signal Monitor..."
            docker-compose -f docker-compose.market-monitor.yml down
            print_success "Market Signal Monitor stopped"
            ;;
        restart)
            check_requirements
            print_info "Restarting Market Signal Monitor..."
            docker-compose -f docker-compose.market-monitor.yml down
            sleep 5
            start_monitor
            show_status
            ;;
        status)
            show_status
            ;;
        logs)
            print_info "Showing Market Signal Monitor logs..."
            echo "Press Ctrl+C to exit"
            echo "================================"
            docker logs -f market-signal-monitor
            ;;
        test)
            test_telegram_config
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown command: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
