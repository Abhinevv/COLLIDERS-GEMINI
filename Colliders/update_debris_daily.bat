@echo off
REM Daily Debris Database Update Script
REM This script updates the debris database from Space-Track.org

cd /d "%~dp0"

echo ========================================
echo Colliders - Daily Debris Update
echo ========================================
echo Started: %date% %time%
echo.

REM Check if virtual environment exists
if not exist "spaceenv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please create it first: python -m venv spaceenv
    exit /b 1
)

REM Check if Space-Track credentials are set
if "%SPACETRACK_USERNAME%"=="" (
    echo WARNING: SPACETRACK_USERNAME environment variable not set
    echo Debris update may fail without Space-Track credentials
    echo.
)

if "%SPACETRACK_PASSWORD%"=="" (
    echo WARNING: SPACETRACK_PASSWORD environment variable not set
    echo Debris update may fail without Space-Track credentials
    echo.
)

REM Run the debris update script
echo Running debris database update...
echo.
spaceenv\Scripts\python.exe populate_db.py

if errorlevel 1 (
    echo.
    echo ERROR: Debris update failed!
    echo Check the error messages above.
    exit /b 1
) else (
    echo.
    echo SUCCESS: Debris database updated successfully!
    echo Completed: %date% %time%
)

echo ========================================
