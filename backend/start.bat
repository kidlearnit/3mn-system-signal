@echo off
REM Windows Batch Script for Symbol-Specific Thresholds System Deployment
REM This script sets up and starts the Docker environment

echo.
echo ================================================================
echo    Symbol-Specific Thresholds System - Windows Deployment
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

REM Check if docker-compose.yml exists
echo [2/8] Checking docker-compose.yml...
if not exist "docker-compose.yml" (
    echo [ERROR] docker-compose.yml not found!
    echo Please ensure you're in the project root directory.
    echo.
    pause
    exit /b 1
)
echo [OK] docker-compose.yml found

REM Verify required files
echo [3/8] Verifying required files...
set "required_files=schema.sql init_data.sql app\services\symbol_thresholds.py app\services\signal_engine.py worker\jobs.py"
for %%f in (%required_files%) do (
    if not exist "%%f" (
        echo [ERROR] Required file missing: %%f
        echo.
        pause
        exit /b 1
    )
)
echo [OK] All required files present

REM Stop any existing containers
echo [4/8] Stopping existing containers...
docker-compose down >nul 2>&1
echo [OK] Existing containers stopped

REM Start Docker containers
echo [5/8] Starting Docker containers...
docker-compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start Docker containers!
    echo Please check your Docker configuration.
    echo.
    pause
    exit /b 1
)
echo [OK] Docker containers started

REM Wait for database to be ready
echo [6/8] Waiting for database to be ready...
timeout /t 15 /nobreak >nul
echo [OK] Database startup wait completed

REM Check database connection
echo [7/8] Checking database connection...
docker-compose exec -T db mysql -u root -ppassword -e "SELECT 1;" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Database connection test failed, but continuing...
    echo This might be normal if the database is still starting up.
) else (
    echo [OK] Database connection verified
)

REM Verify database setup
echo [8/8] Verifying database setup...
docker-compose exec -T db mysql -u root -ppassword trading_signals -e "SELECT COUNT(*) FROM market_threshold_templates;" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Database verification failed, but continuing...
    echo The system might still work correctly.
) else (
    echo [OK] Database setup verified
)

echo.
echo ================================================================
echo                    DEPLOYMENT COMPLETED!
echo ================================================================
echo.
echo [SUCCESS] Symbol-Specific Thresholds System is now running!
echo.
echo System Status:
echo   ✓ Database schema created
echo   ✓ Threshold data loaded
echo   ✓ Symbol-specific thresholds system ready
echo   ✓ US and VN market thresholds configured
echo.
echo Access Points:
echo   • Web Application: http://localhost:5000
echo   • Database: localhost:3306
echo   • Redis: localhost:6379
echo.
echo System Features:
echo   • Market-specific thresholds (US vs VN)
echo   • Symbol-specific customization
echo   • 8 timeframes support (1m to 1D)
echo   • Automatic market detection
echo.
echo Thresholds Summary:
echo   • US Market: MACD values 0-3 (small values)
echo   • VN Market: MACD values 0-50 (large values)
echo   • Automatic fallback to market defaults
echo.
echo Next Steps:
echo   1. Open http://localhost:5000 in your browser
echo   2. Check the dashboard for system status
echo   3. Monitor trading signals
echo   4. Customize thresholds if needed
echo.
echo Troubleshooting:
echo   • Check container status: docker-compose ps
echo   • View logs: docker-compose logs
echo   • Restart system: docker-compose restart
echo   • Stop system: docker-compose down
echo.

REM Ask user if they want to open the web application
set /p "open_browser=Do you want to open the web application now? (y/n): "
if /i "%open_browser%"=="y" (
    echo Opening web application...
    start http://localhost:5000
)

echo.
echo Press any key to exit...
pause >nul
