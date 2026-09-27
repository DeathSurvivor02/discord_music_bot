@echo off
title Spotify AI DJ Desktop
cd /d "%~dp0"

echo ===================================================
echo             SPOTIFY AI DJ DESKTOP
echo ===================================================

:: Check if API server is already running on port 8000
netstat -ano | findstr :8000 >nul
if %errorlevel% neq 0 (
    echo [*] Starting Audio & DJ Commentary Engine...
    start "" /b .\.venv\Scripts\python.exe api_server.py
    timeout /t 2 /nobreak >nul
) else (
    echo [*] Audio Engine is running.
)

:: Check if Mobile/Web app bundler is running on port 8081
netstat -ano | findstr :8081 >nul
if %errorlevel% neq 0 (
    echo [*] Starting Desktop Web App Server...
    cd mobile_app
    start "" /b npx expo start --web --tunnel
    cd ..
    timeout /t 4 /nobreak >nul
) else (
    echo [*] Player App Server is running.
)

echo [*] Opening Spotify AI DJ Window...
:: Launch in standalone app mode using Microsoft Edge / Chrome
start msedge --app=http://localhost:8081 --window-size=460,890

exit
