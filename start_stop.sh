#!/bin/bash

# Linux Shell Script for 3MN Trading Signals System - Start/Stop Control
# This script provides easy start/stop control for the system

set -e  # Exit on any error

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

show_menu() {
    echo ""
    echo "================================================================"
    echo "    3MN Trading Signals System - Start/Stop Control"
    echo "================================================================"
    echo ""
    echo "Please select an option:"
    echo ""
    echo "1. Start System"
    echo "2. Stop System"
    echo "3. Restart System"
    echo "4. Check Status"
    echo "5. View Logs"
    echo "6. Exit"
    echo ""
}

start_system() {
    echo ""
    print_status "Starting 3MN Trading Signals System..."
    if ! docker-compose up -d; then
        print_error "Failed to start system!"
        echo "Please check your Docker configuration."
        echo ""
        return 1
    fi
    print_success "System started successfully!"
    echo ""
    echo "Access Points:"
    echo "  • Web Application: http://localhost:5010"
    echo "  • Workflow Builder: http://localhost:5010/workflow-builder"
    echo "  • Database: localhost:3309"
    echo "  • Redis: localhost:6379"
    echo ""
    read -p "Press Enter to continue..."
}

stop_system() {
    echo ""
    print_status "Stopping 3MN Trading Signals System..."
    if ! docker-compose down; then
        print_error "Failed to stop system!"
        echo ""
        return 1
    fi
    print_success "System stopped successfully!"
    echo ""
    read -p "Press Enter to continue..."
}

restart_system() {
    echo ""
    print_status "Restarting 3MN Trading Signals System..."
    print_status "Stopping system..."
    docker-compose down
    print_status "Starting system..."
    if ! docker-compose up -d; then
        print_error "Failed to restart system!"
        echo "Please check your Docker configuration."
        echo ""
        return 1
    fi
    print_success "System restarted successfully!"
    echo ""
    echo "Access Points:"
    echo "  • Web Application: http://localhost:5010"
    echo "  • Workflow Builder: http://localhost:5010/workflow-builder"
    echo "  • Database: localhost:3309"
    echo "  • Redis: localhost:6379"
    echo ""
    read -p "Press Enter to continue..."
}

check_status() {
    echo ""
    print_status "Checking system status..."
    echo ""
    echo "Container Status:"
    docker-compose ps
    echo ""
    echo "Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
    echo ""
    read -p "Press Enter to continue..."
}

view_logs() {
    echo ""
    echo "Please select logs to view:"
    echo ""
    echo "1. All Services"
    echo "2. Web Service"
    echo "3. Worker Service"
    echo "4. Scheduler Service"
    echo "5. MySQL Service"
    echo "6. Redis Service"
    echo "7. Back to Main Menu"
    echo ""
    read -p "Enter your choice (1-7): " log_choice
    
    case $log_choice in
        1)
            echo ""
            print_status "Viewing all services logs (Press Ctrl+C to exit)..."
            docker-compose logs -f
            ;;
        2)
            echo ""
            print_status "Viewing web service logs (Press Ctrl+C to exit)..."
            docker-compose logs -f web
            ;;
        3)
            echo ""
            print_status "Viewing worker service logs (Press Ctrl+C to exit)..."
            docker-compose logs -f worker
            ;;
        4)
            echo ""
            print_status "Viewing scheduler service logs (Press Ctrl+C to exit)..."
            docker-compose logs -f scheduler
            ;;
        5)
            echo ""
            print_status "Viewing MySQL service logs (Press Ctrl+C to exit)..."
            docker-compose logs -f mysql
            ;;
        6)
            echo ""
            print_status "Viewing Redis service logs (Press Ctrl+C to exit)..."
            docker-compose logs -f redis
            ;;
        7)
            return 0
            ;;
        *)
            print_error "Invalid choice. Please try again."
            echo ""
            view_logs
            ;;
    esac
    echo ""
    read -p "Press Enter to continue..."
}

main() {
    while true; do
        show_menu
        read -p "Enter your choice (1-6): " choice
        
        case $choice in
            1)
                start_system
                ;;
            2)
                stop_system
                ;;
            3)
                restart_system
                ;;
            4)
                check_status
                ;;
            5)
                view_logs
                ;;
            6)
                echo ""
                echo "Goodbye!"
                echo ""
                exit 0
                ;;
            *)
                print_error "Invalid choice. Please try again."
                echo ""
                ;;
        esac
    done
}

# Run main function
main
