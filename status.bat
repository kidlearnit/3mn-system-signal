@echo off
REM Windows Batch Script to Check System Status

echo.
echo ================================================================
echo    Symbol-Specific Thresholds System - Status Check
echo ================================================================
echo.

echo [1/4] Checking Docker Desktop...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Desktop is not running!
    echo Please start Docker Desktop first.
    echo.
    pause
    exit /b 1
)
echo [OK] Docker Desktop is running

echo [2/4] Checking container status...
cd backend
docker-compose ps
echo.

echo [3/4] Checking database connection...
docker-compose exec -T db mysql -u root -ppassword -e "SELECT 1;" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Database connection failed
) else (
    echo [OK] Database connection successful
)

echo [4/4] Checking system data...
docker-compose exec -T db mysql -u root -ppassword trading_signals -e "SELECT COUNT(*) as template_count FROM market_threshold_templates;" 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Could not check system data
) else (
    echo [OK] System data verified
)

echo.
echo ================================================================
echo                    SYSTEM STATUS SUMMARY
echo ================================================================
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
echo Management Commands:
echo   • Start system: start.bat
echo   • Stop system: stop.bat
echo   • Restart system: restart.bat
echo   • Check status: status.bat
echo.
echo Press any key to exit...
pause >nul
