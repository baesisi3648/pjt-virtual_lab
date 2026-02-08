@echo off
REM Virtual Lab - Stop Docker Services
echo ===================================
echo Virtual Lab - Stopping Services
echo ===================================
echo.

cd /d "%~dp0"

echo Stopping PostgreSQL, ChromaDB, and Redis...
docker compose down

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Services stopped successfully!
    echo.
    echo Note: Data is preserved in Docker volumes
    echo To remove all data, run: docker compose down -v
) else (
    echo.
    echo ERROR: Failed to stop services
    exit /b 1
)

pause
