@echo off
REM Windows Batch Script for 3MN Trading Signals System - Start/Stop Control
REM This script provides easy start/stop control for the system

echo.
echo ================================================================
echo    3MN Trading Signals System - Start/Stop Control
echo ================================================================
echo.

:menu
echo Please select an option:
echo.
echo 1. Start System
echo 2. Stop System
echo 3. Restart System
echo 4. Check Status
echo 5. View Logs
echo 6. Exit
echo.
set /p "choice=Enter your choice (1-6): "

if "%choice%"=="1" goto start_system
if "%choice%"=="2" goto stop_system
if "%choice%"=="3" goto restart_system
if "%choice%"=="4" goto check_status
if "%choice%"=="5" goto view_logs
if "%choice%"=="6" goto exit_script
echo Invalid choice. Please try again.
echo.
goto menu

:start_system
echo.
echo Starting 3MN Trading Signals System...
docker-compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start system!
    echo Please check your Docker configuration.
    echo.
    pause
    goto menu
)
echo [SUCCESS] System started successfully!
echo.
echo Access Points:
echo   • Web Application: http://localhost:5010
echo   • Workflow Builder: http://localhost:5010/workflow-builder
echo   • Database: localhost:3309
echo   • Redis: localhost:6379
echo.
pause
goto menu

:stop_system
echo.
echo Stopping 3MN Trading Signals System...
docker-compose down
if %errorlevel% neq 0 (
    echo [ERROR] Failed to stop system!
    echo.
    pause
    goto menu
)
echo [SUCCESS] System stopped successfully!
echo.
pause
goto menu

:restart_system
echo.
echo Restarting 3MN Trading Signals System...
echo Stopping system...
docker-compose down
echo Starting system...
docker-compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] Failed to restart system!
    echo Please check your Docker configuration.
    echo.
    pause
    goto menu
)
echo [SUCCESS] System restarted successfully!
echo.
echo Access Points:
echo   • Web Application: http://localhost:5010
echo   • Workflow Builder: http://localhost:5010/workflow-builder
echo   • Database: localhost:3309
echo   • Redis: localhost:6379
echo.
pause
goto menu

:check_status
echo.
echo Checking system status...
echo.
echo Container Status:
docker-compose ps
echo.
echo Resource Usage:
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
echo.
pause
goto menu

:view_logs
echo.
echo Please select logs to view:
echo.
echo 1. All Services
echo 2. Web Service
echo 3. Worker Service
echo 4. Scheduler Service
echo 5. MySQL Service
echo 6. Redis Service
echo 7. Back to Main Menu
echo.
set /p "log_choice=Enter your choice (1-7): "

if "%log_choice%"=="1" (
    echo.
    echo Viewing all services logs (Press Ctrl+C to exit)...
    docker-compose logs -f
)
if "%log_choice%"=="2" (
    echo.
    echo Viewing web service logs (Press Ctrl+C to exit)...
    docker-compose logs -f web
)
if "%log_choice%"=="3" (
    echo.
    echo Viewing worker service logs (Press Ctrl+C to exit)...
    docker-compose logs -f worker
)
if "%log_choice%"=="4" (
    echo.
    echo Viewing scheduler service logs (Press Ctrl+C to exit)...
    docker-compose logs -f scheduler
)
if "%log_choice%"=="5" (
    echo.
    echo Viewing MySQL service logs (Press Ctrl+C to exit)...
    docker-compose logs -f mysql
)
if "%log_choice%"=="6" (
    echo.
    echo Viewing Redis service logs (Press Ctrl+C to exit)...
    docker-compose logs -f redis
)
if "%log_choice%"=="7" goto menu
if not "%log_choice%"=="1" if not "%log_choice%"=="2" if not "%log_choice%"=="3" if not "%log_choice%"=="4" if not "%log_choice%"=="5" if not "%log_choice%"=="6" if not "%log_choice%"=="7" (
    echo Invalid choice. Please try again.
    echo.
    goto view_logs
)
echo.
pause
goto menu

:exit_script
echo.
echo Goodbye!
echo.
pause
exit /b 0
