@echo off
echo ============================================
echo   Virtual Lab Server Restart Script
echo ============================================
echo.

REM 1. Kill all Python processes on port 8000
echo [1/5] Killing old Python processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo   Killing PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul

REM 2. Delete __pycache__
echo [2/5] Deleting __pycache__ files...
for /d /r "%~dp0" %%d in (__pycache__) do (
    if exist "%%d" (
        rmdir /s /q "%%d" >nul 2>&1
    )
)
echo   Done.

REM 3. Set environment
echo [3/5] Setting environment...
set PYTHONDONTWRITEBYTECACHE=1
cd /d "%~dp0"

REM 4. Disable LangChain auto-instrumentation
echo [4/5] Disabling LangChain tracing...
set LANGCHAIN_TRACING_V2=false
set LANGCHAIN_TRACING=false

REM 5. Start server
echo [5/5] Starting new server...
echo.
echo ============================================
echo   Server starting at http://localhost:8000
echo   Press Ctrl+C to stop
echo ============================================
echo.
venv\Scripts\python.exe -B -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
