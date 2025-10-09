@echo off
REM Windows Batch Script to Stop Symbol-Specific Thresholds System

echo.
echo ================================================================
echo    Stopping Symbol-Specific Thresholds System
echo ================================================================
echo.

echo [1/3] Stopping Docker containers...
cd backend
docker-compose down
if %errorlevel% neq 0 (
    echo [WARNING] Some containers might not have stopped cleanly
) else (
    echo [OK] All containers stopped successfully
)

echo [2/3] Cleaning up...
docker-compose down --volumes --remove-orphans >nul 2>&1
echo [OK] Cleanup completed

echo [3/3] Checking system status...
docker-compose ps
echo.

echo ================================================================
echo                    SYSTEM STOPPED!
echo ================================================================
echo.
echo The Symbol-Specific Thresholds System has been stopped.
echo.
echo To start the system again, run: start.bat
echo.
echo Press any key to exit...
pause >nul
