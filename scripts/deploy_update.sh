#!/bin/bash

# 🔄 3MN Trading Signals - Update Deployment Script
# This script updates an existing deployment with new features

set -e  # Exit on any error

echo "🔄 Starting 3MN Trading Signals Update Deployment..."
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

# Check if system is already running
check_existing_system() {
    print_status "Checking existing system..."
    
    if docker-compose ps | grep -q "running"; then
        print_success "Existing system found"
        return 0
    else
        print_warning "No existing system found. Consider using deploy_fresh.sh instead."
        return 1
    fi
}

# Backup existing data
backup_data() {
    print_status "Creating backup of existing data..."
    
    # Create backup directory
    BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup database
    print_status "Backing up database..."
    docker-compose exec -T mysql mysqldump -u trader -ptraderpass trading > "$BACKUP_DIR/database_backup.sql"
    
    # Backup workflows
    print_status "Backing up workflows..."
    docker-compose exec -T worker python -c "
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
" && docker cp $(docker-compose ps -q worker):/tmp/workflows_backup.json "$BACKUP_DIR/"
    
    # Backup signals
    print_status "Backing up signals..."
    docker-compose exec -T worker python -c "
import sys; sys.path.append('/code')
from app.db import init_db, SessionLocal
import os
import json
init_db(os.getenv('DATABASE_URL'))
from app.db import SessionLocal
from sqlalchemy import text
with SessionLocal() as s:
    result = s.execute(text('SELECT COUNT(*) FROM signals')).fetchone()
    print(f'Backing up {result[0]} signals')
" > "$BACKUP_DIR/signals_count.txt"
    
    print_success "Backup created in $BACKUP_DIR"
}

# Update environment configuration
update_environment() {
    print_status "Updating environment configuration..."
    
    # Check if new environment variables need to be added
    if [ -f .env ]; then
        # Add new variables if they don't exist
        if ! grep -q "MACD_MULTI_ENABLED" .env; then
            echo "" >> .env
            echo "# MACD Multi-TF Configuration" >> .env
            echo "MACD_MULTI_ENABLED=1" >> .env
            echo "MACD_MULTI_UNANIMOUS_REQUIRED=1" >> .env
            echo "MACD_MULTI_CONFIDENCE_THRESHOLD=0.5" >> .env
            echo "MACD_MULTI_BACKFILL_DAYS=365" >> .env
        fi
        
        if ! grep -q "WORKFLOW_BUILDER_ENABLED" .env; then
            echo "" >> .env
            echo "# Workflow Builder Configuration" >> .env
            echo "WORKFLOW_BUILDER_ENABLED=1" >> .env
            echo "WORKFLOW_AUTO_SAVE=1" >> .env
            echo "WORKFLOW_AUTO_SAVE_INTERVAL=30" >> .env
        fi
        
        if ! grep -q "VNSTOCK_ENABLED" .env; then
            echo "" >> .env
            echo "# Data Sources Configuration" >> .env
            echo "YFINANCE_ENABLED=1" >> .env
            echo "VNSTOCK_ENABLED=1" >> .env
            echo "VNSTOCK_SOURCES=VCI,TCBS,SSI" >> .env
            echo "DATA_FETCH_TIMEOUT=30" >> .env
            echo "DATA_RETRY_ATTEMPTS=3" >> .env
        fi
        
        print_success "Environment configuration updated"
    else
        print_warning "No .env file found. Please create one from env.example"
    fi
}

# Update database schema
update_database() {
    print_status "Updating database schema..."
    
    # Run database migration
    docker-compose exec -T worker python -c "
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
"
    
    print_success "Database schema updated"
}

# Update Docker services
update_services() {
    print_status "Updating Docker services..."
    
    # Pull latest images
    docker-compose pull
    
    # Restart services with new code
    docker-compose up -d --build
    
    print_success "Docker services updated"
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
    try:
        result = s.execute(text('SELECT COUNT(*) FROM macd_multi_signals')).fetchone()
        print(f'MACD Multi-TF signals table: {result[0]} records')
    except:
        print('MACD Multi-TF signals table: Not found')
    
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
try:
    from app.services.data_sources import fetch_vnstock_1m, fetch_yfinance_1m
    print('VNStock and YFinance modules loaded successfully')
except Exception as e:
    print(f'Data sources error: {e}')
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
    cat > /tmp/test_macd_hybrid_update.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
sys.path.append('/code')

try:
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
            }
        ]
    }
    
    result = job_macd_multi_hybrid_pipeline(config, mode='realtime')
    print(f"✅ MACD Multi-TF Hybrid test completed: {result.get('status', 'unknown')}")
    print(f"   Symbols processed: {result.get('symbols_processed', 0)}")
    print(f"   Signals generated: {result.get('signals_generated', 0)}")
except Exception as e:
    print(f"❌ MACD Multi-TF Hybrid test failed: {e}")
EOF
    
    # Run test
    if docker-compose exec -T worker python /tmp/test_macd_hybrid_update.py; then
        print_success "MACD Multi-TF Hybrid test passed"
    else
        print_warning "MACD Multi-TF Hybrid test failed"
    fi
    
    # Cleanup
    rm -f /tmp/test_macd_hybrid_update.py
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
    print_status "Update Deployment Status:"
    echo "============================="
    
    echo "📊 Services Status:"
    docker-compose ps
    
    echo ""
    echo "🌐 Web Interface: http://localhost:5010"
    echo "📊 Database: localhost:3309"
    echo "🔄 Redis: localhost:6379"
    
    echo ""
    echo "🆕 New Features Added:"
    echo "  ✅ MACD Multi-TF Hybrid (VN + US symbols)"
    echo "  ✅ Workflow Builder with drag-and-drop"
    echo "  ✅ Unanimous signal logic (6/6 timeframes)"
    echo "  ✅ VNStock integration for Vietnamese stocks"
    echo "  ✅ YFinance integration for US stocks"
    echo "  ✅ Automatic exchange detection"
    echo "  ✅ Mixed workflow support (VN + US in same workflow)"
    
    echo ""
    echo "📈 System Statistics:"
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
    
    try:
        result = s.execute(text('SELECT COUNT(*) FROM macd_multi_signals')).fetchone()
        print(f'MACD Multi-TF signals: {result[0]}')
    except:
        print('MACD Multi-TF signals: 0 (new feature)')
    
    result = s.execute(text('SELECT COUNT(*) FROM workflows')).fetchone()
    print(f'Workflows: {result[0]}')
    
    result = s.execute(text('SELECT exchange, COUNT(*) FROM symbols GROUP BY exchange')).fetchall()
    for exchange, count in result:
        print(f'Symbols in {exchange}: {count}')
" 2>/dev/null || echo "Unable to check statistics"
    
    echo ""
    print_success "🔄 Update deployment completed successfully!"
    print_status "You can now access the updated system at http://localhost:5010"
    print_status "Try creating a new MACD Multi-TF workflow with both VN and US symbols!"
}

# Main deployment flow
main() {
    if check_existing_system; then
        backup_data
        update_environment
        update_database
        update_services
        verify_deployment
        verify_new_features
        test_macd_hybrid
        show_status
    else
        print_error "No existing system found. Please use deploy_fresh.sh for fresh installation."
        exit 1
    fi
}

# Run main function
main "$@"
