@echo off
REM Virtual Lab - Start Docker Services
echo ===================================
echo Virtual Lab - Starting Services
echo ===================================
echo.

cd /d "%~dp0"

echo Starting PostgreSQL, ChromaDB, and Redis...
docker compose up -d

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Services started successfully!
    echo.
    echo Waiting 10 seconds for services to initialize...
    timeout /t 10 /nobreak > nul
    echo.
    echo Checking service status...
    docker compose ps
    echo.
    echo ===================================
    echo Services are ready!
    echo ===================================
    echo.
    echo PostgreSQL: localhost:5432
    echo ChromaDB:   http://localhost:8001
    echo Redis:      localhost:6379
    echo.
    echo Run 'python scripts\healthcheck.py' for detailed health check
) else (
    echo.
    echo ERROR: Failed to start services
    echo Check Docker is running and try again
    exit /b 1
)

pause
