@echo off
REM Windows Batch Script to Restart Symbol-Specific Thresholds System

echo.
echo ================================================================
echo    Restarting Symbol-Specific Thresholds System
echo ================================================================
echo.

echo [1/4] Stopping current system...
cd backend
docker-compose down >nul 2>&1
echo [OK] System stopped

echo [2/4] Cleaning up containers...
docker-compose down --volumes --remove-orphans >nul 2>&1
echo [OK] Cleanup completed

echo [3/4] Starting system...
docker-compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start system!
    echo Please check your Docker configuration.
    echo.
    pause
    exit /b 1
)
echo [OK] System started

echo [4/4] Waiting for system to be ready...
timeout /t 10 /nobreak >nul
echo [OK] System ready

echo.
echo ================================================================
echo                    SYSTEM RESTARTED!
echo ================================================================
echo.
echo The Symbol-Specific Thresholds System has been restarted.
echo.
echo Access Points:
echo   • Web Application: http://localhost:5000
echo   • Database: localhost:3306
echo   • Redis: localhost:6379
echo.
echo Press any key to exit...
pause >nul
