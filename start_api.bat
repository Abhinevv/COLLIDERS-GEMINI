@echo off
REM Start AstroCleanAI API Server
REM Double-click this file or run from terminal

REM Change to script directory
cd /d "%~dp0"

echo ========================================
echo Starting AstroCleanAI API Server
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "spaceenv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please create it first: python -m venv spaceenv
    pause
    exit /b 1
)

REM Check if Flask is installed
spaceenv\Scripts\python.exe -c "import flask" 2>nul
if errorlevel 1 (
    echo Installing Flask and dependencies...
    spaceenv\Scripts\python.exe -m pip install flask flask-cors
    echo.
)

REM Start the API server
echo Starting server on http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

spaceenv\Scripts\python.exe api.py

pause
