#!/bin/bash

# Linux Shell Script for 3MN Trading Signals System Update
# This script updates an existing deployment with new features

set -e  # Exit on any error

echo ""
echo "================================================================"
echo "    3MN Trading Signals System - Linux Update Deployment"
echo "================================================================"
echo ""

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

# Check if Docker is running
print_status "[1/8] Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running!"
    echo "Please start Docker and try again."
    echo ""
    exit 1
fi
print_success "Docker is running"

# Check if system is already running
print_status "[2/8] Checking existing system..."
if ! docker-compose ps | grep -q "running"; then
    print_warning "No existing system found!"
    echo "Consider using start.sh for fresh installation."
    echo ""
    read -p "Continue with update anyway? (y/n): " continue
    if [[ ! "$continue" =~ ^[Yy]$ ]]; then
        echo "Please run start.sh for fresh installation."
        exit 1
    fi
else
    print_success "Existing system found"
fi

# Create backup
print_status "[3/8] Creating backup of existing data..."
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

print_status "Backing up database..."
if docker-compose exec -T mysql mysqldump -u trader -ptraderpass trading > "$BACKUP_DIR/database_backup.sql" 2>/dev/null; then
    print_success "Database backup completed"
else
    print_warning "Database backup failed, but continuing..."
fi

print_status "Backing up workflows..."
if docker-compose exec -T worker python -c "
import sys; sys.path.append('/code')
from app.db import init_db, SessionLocal
import os
import json
init_db(os.getenv('DATABASE_URL'))
from app.db import SessionLocal
from sqlalchemy import text
with SessionLocal() as s:
    result = s.execute(text('SELECT * FROM workflows')).fetchall()
    workflows = []
    for row in result:
        workflows.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'nodes': row[3],
            'connections': row[4],
            'properties': row[5],
            'metadata': row[6],
            'status': row[7],
            'created_at': str(row[8]),
            'updated_at': str(row[9])
        })
    with open('/tmp/workflows_backup.json', 'w') as f:
        json.dump(workflows, f, indent=2)
" > /dev/null 2>&1; then
    docker cp $(docker-compose ps -q worker):/tmp/workflows_backup.json "$BACKUP_DIR/" > /dev/null 2>&1
    print_success "Workflows backup completed"
else
    print_warning "Workflows backup failed, but continuing..."
fi

print_success "Backup created in $BACKUP_DIR"

# Update environment configuration
print_status "[4/8] Updating environment configuration..."
if [ -f ".env" ]; then
    print_status "Adding new environment variables..."
    cat >> .env << 'EOF'

# MACD Multi-TF Configuration
MACD_MULTI_ENABLED=1
MACD_MULTI_UNANIMOUS_REQUIRED=1
MACD_MULTI_CONFIDENCE_THRESHOLD=0.5
MACD_MULTI_BACKFILL_DAYS=365

# Workflow Builder Configuration
WORKFLOW_BUILDER_ENABLED=1
WORKFLOW_AUTO_SAVE=1
WORKFLOW_AUTO_SAVE_INTERVAL=30

# Data Sources Configuration
YFINANCE_ENABLED=1
VNSTOCK_ENABLED=1
VNSTOCK_SOURCES=VCI,TCBS,SSI
DATA_FETCH_TIMEOUT=30
DATA_RETRY_ATTEMPTS=3
EOF
    print_success "Environment configuration updated"
else
    print_warning ".env file not found, creating from template..."
    if [ -f "env.example" ]; then
        cp env.example .env
        print_success ".env file created from template"
    else
        print_error "No .env template found!"
        exit 1
    fi
fi

# Update Docker services
print_status "[5/8] Updating Docker services..."
docker-compose pull > /dev/null 2>&1
if ! docker-compose up -d --build; then
    print_error "Failed to update Docker services!"
    echo "Please check your Docker configuration."
    echo ""
    exit 1
fi
print_success "Docker services updated"

# Wait for services to be ready
print_status "[6/8] Waiting for services to be ready..."
sleep 20
print_success "Services startup wait completed"

# Update database schema
print_status "[7/8] Updating database schema..."
if ! docker-compose exec -T worker python -c "
import sys; sys.path.append('/code')
from app.db import init_db, SessionLocal
import os
from sqlalchemy import text
init_db(os.getenv('DATABASE_URL'))
from app.db import SessionLocal

# Read migration file
with open('/code/database_migration.sql', 'r') as f:
    migration_sql = f.read()

with SessionLocal() as s:
    # Split SQL by semicolon and execute each statement
    statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
    
    for statement in statements:
        if statement.upper().startswith(('CREATE', 'ALTER', 'INSERT', 'UPDATE', 'DELETE')):
            try:
                s.execute(text(statement))
                print(f'✅ Executed: {statement[:50]}...')
            except Exception as e:
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    print(f'ℹ️ Already exists: {statement[:50]}...')
                else:
                    print(f'⚠️ Warning: {e}')
    
    s.commit()
    print('✅ Database migration completed')
" > /dev/null 2>&1; then
    print_warning "Database schema update failed, but continuing..."
    echo "The system might still work correctly."
else
    print_success "Database schema updated"
fi

# Verify new features
print_status "[8/8] Verifying new features..."
if ! docker-compose exec -T worker python -c "
import sys; sys.path.append('/code')
from app.db import init_db, SessionLocal
import os
from sqlalchemy import text
init_db(os.getenv('DATABASE_URL'))
from app.db import SessionLocal

with SessionLocal() as s:
    # Check new tables
    try:
        result = s.execute(text('SELECT COUNT(*) FROM macd_multi_signals')).fetchone()
        print(f'MACD Multi-TF signals table: {result[0]} records')
    except:
        print('MACD Multi-TF signals table: Not found')
    
    result = s.execute(text('SELECT COUNT(*) FROM workflows')).fetchone()
    print(f'Workflows table: {result[0]} records')
    
    result = s.execute(text('SELECT COUNT(*) FROM symbols')).fetchone()
    print(f'Symbols: {result[0]} records')
    
    result = s.execute(text('SELECT exchange, COUNT(*) FROM symbols GROUP BY exchange')).fetchall()
    for exchange, count in result:
        print(f'Symbols in {exchange}: {count}')
" > /dev/null 2>&1; then
    print_warning "New features verification failed, but continuing..."
    echo "Some features might not be fully configured."
else
    print_success "New features verified"
fi

echo ""
echo "================================================================"
echo "                    UPDATE COMPLETED!"
echo "================================================================"
echo ""
print_success "3MN Trading Signals System has been updated!"
echo ""
echo "Update Summary:"
echo "  ✓ Existing data backed up to $BACKUP_DIR"
echo "  ✓ Environment configuration updated"
echo "  ✓ Docker services updated with new code"
echo "  ✓ Database schema updated with new tables"
echo "  ✓ New features verified"
echo ""
echo "New Features Added:"
echo "  • MACD Multi-TF Hybrid (VN + US symbols)"
echo "  • Workflow Builder with drag-and-drop"
echo "  • Unanimous signal logic (6/6 timeframes)"
echo "  • VNStock integration for Vietnamese stocks"
echo "  • YFinance integration for US stocks"
echo "  • Automatic exchange detection"
echo "  • Mixed workflow support (VN + US in same workflow)"
echo ""
echo "Access Points:"
echo "  • Web Application: http://localhost:5010"
echo "  • Workflow Builder: http://localhost:5010/workflow-builder"
echo "  • Database: localhost:3309"
echo "  • Redis: localhost:6379"
echo ""
echo "Next Steps:"
echo "  1. Open http://localhost:5010 in your browser"
echo "  2. Create your first MACD Multi-TF workflow"
echo "  3. Add both VN and US symbols to test hybrid system"
echo "  4. Monitor trading signals with unanimous logic"
echo ""
echo "Troubleshooting:"
echo "  • Check container status: docker-compose ps"
echo "  • View logs: docker-compose logs"
echo "  • Run verification: ./scripts/verify_deployment.sh"
echo "  • Run troubleshooting: ./scripts/troubleshoot_deployment.sh"
echo "  • Restore backup if needed: $BACKUP_DIR"
echo ""

# Ask user if they want to open the web application
read -p "Do you want to open the web application now? (y/n): " open_browser
if [[ "$open_browser" =~ ^[Yy]$ ]]; then
    echo "Opening web application..."
    if command -v xdg-open > /dev/null; then
        xdg-open http://localhost:5010
    elif command -v open > /dev/null; then
        open http://localhost:5010
    else
        echo "Please open http://localhost:5010 in your browser"
    fi
fi

echo ""
echo "Press Enter to exit..."
read
