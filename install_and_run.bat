@echo off
REM Install dependencies and run AstroCleanAI
REM This works in Command Prompt and bypasses PowerShell issues

echo ========================================
echo AstroCleanAI - Installing Dependencies
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "spaceenv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv spaceenv
    echo.
)

REM Install dependencies
echo Installing dependencies from requirements.txt...
echo.
spaceenv\Scripts\python.exe -m pip install --upgrade pip
spaceenv\Scripts\python.exe -m pip install -r requirements.txt

echo.
echo ========================================
echo Dependencies installed!
echo ========================================
echo.
echo Now running AstroCleanAI...
echo.

REM Run the program
spaceenv\Scripts\python.exe main.py

echo.
echo ========================================
echo Done!
echo ========================================
echo.
pause
