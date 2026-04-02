@echo off
title BLOODSPIRE League Server

echo.
echo  ================================================================
echo    BLOODSPIRE LEAGUE SERVER
echo  ================================================================
echo.
echo  This starts the multiplayer league server that other players
echo  connect to.  You still run START_GAME.bat to play yourself.
echo.

:: Prompt for host password
set /p HOST_PW="  Enter a host/admin password for the league server: "
if "%HOST_PW%"=="" (
    echo  ERROR: Password cannot be blank.
    pause
    exit /b 1
)

echo.
echo  Starting league server on port 8766...
echo  Keep this window open while players are connected.
echo  Press Ctrl+C to stop.
echo.
echo  Admin panel:  http://localhost:8766/admin
echo.
echo  Share your IP address with other players so they can connect.
echo  (If using Tailscale, share your Tailscale IP: 100.x.x.x)
echo  Players should enter:  http://YOUR_IP:8766
echo.

cd /d "%~dp0"
python league_server.py --host-password "%HOST_PW%"
pause
