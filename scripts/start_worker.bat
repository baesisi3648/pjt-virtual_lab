@echo off
REM Celery Worker Startup Script (Windows)

echo =========================================
echo   Virtual Lab - Celery Worker Startup
echo =========================================
echo.

REM Check if Redis is running
redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo ERROR: Redis is not running!
    echo Please start Redis first:
    echo   docker-compose up -d redis
    pause
    exit /b 1
)

echo [OK] Redis connection verified
echo.

REM Start Celery worker
echo Starting Celery worker...
echo Press Ctrl+C to stop
echo.

celery -A celery_app worker ^
    --loglevel=info ^
    --pool=solo ^
    --concurrency=1 ^
    --max-tasks-per-child=50 ^
    --task-events ^
    --without-gossip ^
    --without-mingle ^
    --without-heartbeat

pause
