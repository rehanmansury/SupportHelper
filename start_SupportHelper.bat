@echo off
REM Run SupportHelper
setlocal

REM Set the working directory to the script's directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Run the application
echo Starting SupportHelper...
python main.py

REM Keep the window open if there's an error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application closed with error code %ERRORLEVEL%
    pause
)

endlocal
