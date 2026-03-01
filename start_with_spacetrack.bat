@echo off
echo ========================================
echo Starting AstroCleanAI with Space-Track
echo ========================================
echo.

REM Set your Space-Track credentials here
set SPACETRACK_USER=riddheshmorankar@53
set SPACETRACK_PASS=QWERTYuiop12345678901234567890

echo Credentials set:
echo Username: %SPACETRACK_USER%
echo Password: ********
echo.

REM Check if credentials are still default
if "%SPACETRACK_USER%"=="YOUR_USERNAME" (
    echo ERROR: Please edit start_with_spacetrack.bat and set your credentials!
    echo.
    echo 1. Open start_with_spacetrack.bat in a text editor
    echo 2. Replace YOUR_USERNAME with your Space-Track username
    echo 3. Replace YOUR_PASSWORD with your Space-Track password
    echo 4. Save and run this file again
    echo.
    pause
    exit /b 1
)

echo Activating virtual environment...
call spaceenv\Scripts\activate.bat

echo.
echo Starting API server with Space-Track integration...
echo.
python api.py

pause
