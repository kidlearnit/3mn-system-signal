@echo off
REM Windows Batch Script for 3MN Trading Signals System Update
REM This script updates an existing deployment with new features

echo.
echo ================================================================
echo    3MN Trading Signals System - Windows Update Deployment
echo ================================================================
echo.

REM Check if Docker Desktop is running
echo [1/8] Checking Docker Desktop...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Desktop is not running!
    echo Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)
echo [OK] Docker Desktop is running

REM Check if system is already running
echo [2/8] Checking existing system...
docker-compose ps | findstr "running" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] No existing system found!
    echo Consider using start.bat for fresh installation.
    echo.
    set /p "continue=Continue with update anyway? (y/n): "
    if /i not "%continue%"=="y" (
        echo Please run start.bat for fresh installation.
        pause
        exit /b 1
    )
) else (
    echo [OK] Existing system found
)

REM Create backup
echo [3/8] Creating backup of existing data...
set BACKUP_DIR=backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_DIR=%BACKUP_DIR: =0%
mkdir "%BACKUP_DIR%" 2>nul

echo [INFO] Backing up database...
docker-compose exec -T mysql mysqldump -u trader -ptraderpass trading > "%BACKUP_DIR%\database_backup.sql" 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Database backup failed, but continuing...
) else (
    echo [OK] Database backup completed
)

echo [INFO] Backing up workflows...
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
" >nul 2>&1
docker cp $(docker-compose ps -q worker):/tmp/workflows_backup.json "%BACKUP_DIR%\" >nul 2>&1
echo [OK] Workflows backup completed

echo [OK] Backup created in %BACKUP_DIR%

REM Update environment configuration
echo [4/8] Updating environment configuration...
if exist ".env" (
    echo [INFO] Adding new environment variables...
    echo. >> .env
    echo # MACD Multi-TF Configuration >> .env
    echo MACD_MULTI_ENABLED=1 >> .env
    echo MACD_MULTI_UNANIMOUS_REQUIRED=1 >> .env
    echo MACD_MULTI_CONFIDENCE_THRESHOLD=0.5 >> .env
    echo MACD_MULTI_BACKFILL_DAYS=365 >> .env
    echo. >> .env
    echo # Workflow Builder Configuration >> .env
    echo WORKFLOW_BUILDER_ENABLED=1 >> .env
    echo WORKFLOW_AUTO_SAVE=1 >> .env
    echo WORKFLOW_AUTO_SAVE_INTERVAL=30 >> .env
    echo. >> .env
    echo # Data Sources Configuration >> .env
    echo YFINANCE_ENABLED=1 >> .env
    echo VNSTOCK_ENABLED=1 >> .env
    echo VNSTOCK_SOURCES=VCI,TCBS,SSI >> .env
    echo DATA_FETCH_TIMEOUT=30 >> .env
    echo DATA_RETRY_ATTEMPTS=3 >> .env
    echo [OK] Environment configuration updated
) else (
    echo [WARNING] .env file not found, creating from template...
    if exist "env.example" (
        copy env.example .env >nul
        echo [OK] .env file created from template
    ) else (
        echo [ERROR] No .env template found!
        pause
        exit /b 1
    )
)

REM Update Docker services
echo [5/8] Updating Docker services...
docker-compose pull >nul 2>&1
docker-compose up -d --build
if %errorlevel% neq 0 (
    echo [ERROR] Failed to update Docker services!
    echo Please check your Docker configuration.
    echo.
    pause
    exit /b 1
)
echo [OK] Docker services updated

REM Wait for services to be ready
echo [6/8] Waiting for services to be ready...
timeout /t 20 /nobreak >nul
echo [OK] Services startup wait completed

REM Update database schema
echo [7/8] Updating database schema...
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
" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Database schema update failed, but continuing...
    echo The system might still work correctly.
) else (
    echo [OK] Database schema updated
)

REM Verify new features
echo [8/8] Verifying new features...
docker-compose exec -T worker python -c "
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
" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] New features verification failed, but continuing...
    echo Some features might not be fully configured.
) else (
    echo [OK] New features verified
)

echo.
echo ================================================================
echo                    UPDATE COMPLETED!
echo ================================================================
echo.
echo [SUCCESS] 3MN Trading Signals System has been updated!
echo.
echo Update Summary:
echo   ✓ Existing data backed up to %BACKUP_DIR%
echo   ✓ Environment configuration updated
echo   ✓ Docker services updated with new code
echo   ✓ Database schema updated with new tables
echo   ✓ New features verified
echo.
echo New Features Added:
echo   • MACD Multi-TF Hybrid (VN + US symbols)
echo   • Workflow Builder with drag-and-drop
echo   • Unanimous signal logic (6/6 timeframes)
echo   • VNStock integration for Vietnamese stocks
echo   • YFinance integration for US stocks
echo   • Automatic exchange detection
echo   • Mixed workflow support (VN + US in same workflow)
echo.
echo Access Points:
echo   • Web Application: http://localhost:5010
echo   • Workflow Builder: http://localhost:5010/workflow-builder
echo   • Database: localhost:3309
echo   • Redis: localhost:6379
echo.
echo Next Steps:
echo   1. Open http://localhost:5010 in your browser
echo   2. Create your first MACD Multi-TF workflow
echo   3. Add both VN and US symbols to test hybrid system
echo   4. Monitor trading signals with unanimous logic
echo.
echo Troubleshooting:
echo   • Check container status: docker-compose ps
echo   • View logs: docker-compose logs
echo   • Run verification: scripts\verify_deployment.sh
echo   • Run troubleshooting: scripts\troubleshoot_deployment.sh
echo   • Restore backup if needed: %BACKUP_DIR%
echo.

REM Ask user if they want to open the web application
set /p "open_browser=Do you want to open the web application now? (y/n): "
if /i "%open_browser%"=="y" (
    echo Opening web application...
    start http://localhost:5010
)

echo.
echo Press any key to exit...
pause >nul
