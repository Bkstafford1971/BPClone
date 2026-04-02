@echo off
title BLOODSPIRE

:: Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python is not installed or not in your PATH.
    echo.
    echo  Please install Python from https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

:: Check Python version is 3.8+
python -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python 3.8 or newer is required.
    echo  Please update Python from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo.
echo  Starting BLOODSPIRE...
echo  Your browser will open automatically.
echo  Keep this window open while playing.
echo  Press Ctrl+C in this window to stop the server.
echo.

cd /d "%~dp0"
python gui_server.py
pause
