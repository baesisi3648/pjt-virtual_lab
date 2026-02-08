@echo off
REM Production Deployment Script for Windows
REM Usage: scripts\deploy.bat

echo ============================================================
echo Virtual Lab Production Deployment
echo ============================================================
echo.

REM Check if .env.production exists
if not exist .env.production (
    echo ERROR: .env.production not found
    echo Please copy .env.production.example to .env.production and configure it
    echo.
    echo   copy .env.production.example .env.production
    echo   notepad .env.production
    echo.
    exit /b 1
)

REM Validate environment
echo [Step 1/5] Validating environment variables...
python scripts\validate_env.py
if errorlevel 1 (
    echo ERROR: Environment validation failed
    exit /b 1
)
echo.

REM Check Docker
echo [Step 2/5] Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running. Please start Docker Desktop.
    exit /b 1
)
echo Docker is running
echo.

REM Check Docker Compose
echo [Step 3/5] Checking Docker Compose...
docker-compose version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Compose not found. Please install Docker Compose.
    exit /b 1
)
echo Docker Compose is available
echo.

REM Build and start services
echo [Step 4/5] Building and starting services...
echo This may take several minutes on first run...
docker-compose -f docker-compose.prod.yml up -d --build
if errorlevel 1 (
    echo ERROR: Failed to start services
    exit /b 1
)
echo.

REM Wait for services
echo [Step 5/5] Waiting for services to be healthy...
echo This may take 1-2 minutes...
timeout /t 10 /nobreak >nul

echo.
echo ============================================================
echo Deployment Successful!
echo ============================================================
echo.
echo Services status:
docker-compose -f docker-compose.prod.yml ps
echo.
echo Access URLs:
echo   - Frontend:  http://localhost
echo   - Backend:   http://localhost/api/health
echo   - Nginx:     http://localhost/health
echo.
echo To view logs:
echo   docker-compose -f docker-compose.prod.yml logs -f
echo.
echo To stop services:
echo   docker-compose -f docker-compose.prod.yml down
echo.
