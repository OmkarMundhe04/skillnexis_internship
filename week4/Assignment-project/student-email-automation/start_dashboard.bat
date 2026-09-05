@echo off
title Student Email Automation - Web Dashboard
cd /d "%~dp0"

echo ===================================================
echo     Student Email Automation - Web Dashboard
echo ===================================================
echo.
echo Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not found in your system PATH!
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

echo Starting MailPulse Dashboard on http://localhost:8000 ...
echo Press Ctrl+C anytime to stop the server.
echo.

:: Open browser automatically after 2 seconds
start "" timeout /t 2 /nobreak >nul & start http://localhost:8000

python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
pause
