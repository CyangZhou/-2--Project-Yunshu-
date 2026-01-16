@echo off
echo Starting Yunshu System (Docker Mode)...

:: Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

:: Build and start containers
docker-compose up -d --build

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo Yunshu Web UI started successfully!
    echo Access URL: http://localhost:8765
    echo ========================================================
    echo.
) else (
    echo.
    echo Error: Failed to start containers.
)

pause
