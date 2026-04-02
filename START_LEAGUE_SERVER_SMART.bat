@echo off
REM START_LEAGUE_SERVER_SMART.bat - Launches the League Server with automatic browser closure handling
REM On Windows, this will start the server and open the browser
REM Close the browser to automatically stop the server and exit

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.7+ from python.org
    pause
    exit /b 1
)

echo ============================================================
echo BLOODSPIRE League Server Launcher
echo ============================================================
echo.

REM Run the launcher
python "%SCRIPT_DIR%launch_league.py"

if errorlevel 1 (
    echo.
    echo [ERROR] Launcher failed
    pause
)

endlocal
