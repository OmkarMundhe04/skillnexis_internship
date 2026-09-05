@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Student Email Automation Tool

echo ========================================================
echo             STUDENT EMAIL AUTOMATION TOOL              
echo ========================================================
echo.

:: 1. Activate virtual environment if present
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment: .venv
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment: venv
    call venv\Scripts\activate.bat
)

:: 2. Check if python is accessible
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not found in system PATH.
    echo Please install Python 3.9+ from https://www.python.org/
    echo.
    pause
    exit /b 1
)

:: 3. Present Menu
echo Choose an option:
echo   [1] Dry-Run Simulation (Safe test - default)
echo   [2] Live Email Dispatch (Requires .env credentials)
echo   [3] Run Automated Test Suite (10 test cases)
echo   [4] Install/Update Dependencies (pip install -r requirements.txt)
echo   [5] Exit
echo.
set /p choice="Enter choice [1-5] (Press Enter for 1): "

if "%choice%"=="" set choice=1
set choice=%choice: =%

echo.
if "%choice%"=="1" (
    echo Starting DRY RUN simulation...
    echo --------------------------------------------------------
    python email_automation.py --dry-run
) else if "%choice%"=="2" (
    echo Starting LIVE dispatch...
    echo --------------------------------------------------------
    python email_automation.py --live
) else if "%choice%"=="3" (
    echo Running automated unit tests...
    echo --------------------------------------------------------
    python -m unittest discover tests
) else if "%choice%"=="4" (
    echo Installing requirements...
    echo --------------------------------------------------------
    python -m pip install -r requirements.txt
) else if "%choice%"=="5" (
    echo Exiting.
    exit /b 0
) else (
    echo Invalid choice. Running default DRY RUN simulation...
    echo --------------------------------------------------------
    python email_automation.py --dry-run
)

echo.
echo ========================================================
echo Execution completed.
pause
