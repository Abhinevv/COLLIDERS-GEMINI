@echo off
REM Setup Windows Task Scheduler for Daily Debris Updates
REM Run this script as Administrator to create the scheduled task

echo ========================================
echo Setup Daily Debris Update Task
echo ========================================
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM Get the current directory
set SCRIPT_DIR=%~dp0
set SCRIPT_PATH=%SCRIPT_DIR%update_debris_daily.bat

echo Script location: %SCRIPT_PATH%
echo.

REM Create the scheduled task
echo Creating scheduled task...
schtasks /create /tn "AstroCleanAI Daily Debris Update" /tr "\"%SCRIPT_PATH%\"" /sc daily /st 03:00 /ru SYSTEM /f

if errorlevel 1 (
    echo.
    echo ERROR: Failed to create scheduled task!
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS: Scheduled task created!
echo ========================================
echo.
echo Task Name: AstroCleanAI Daily Debris Update
echo Schedule: Daily at 3:00 AM
echo Script: %SCRIPT_PATH%
echo.
echo The debris database will be automatically updated every day at 3:00 AM.
echo.
echo To view or modify the task:
echo 1. Open Task Scheduler (taskschd.msc)
echo 2. Look for "AstroCleanAI Daily Debris Update"
echo.
echo To run the update manually:
echo - Run update_debris_daily.bat
echo.
echo IMPORTANT: Make sure to set these environment variables:
echo - SPACETRACK_USERNAME (your Space-Track.org username)
echo - SPACETRACK_PASSWORD (your Space-Track.org password)
echo.
echo You can set them in System Properties ^> Environment Variables
echo.
pause
