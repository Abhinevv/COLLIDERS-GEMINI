@echo off
REM Simple batch file to run AstroCleanAI - No PowerShell needed!
REM Just double-click this file or run it from Command Prompt

echo ========================================
echo AstroCleanAI - Running Program
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "spaceenv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo.
    echo Please create it first:
    echo   python -m venv spaceenv
    echo.
    pause
    exit /b 1
)

REM Use Python from virtual environment directly (no activation needed)
echo Using Python from virtual environment...
echo.

REM Check if dependencies are installed
echo Checking dependencies...
spaceenv\Scripts\python.exe -c "import numpy, scipy, plotly, sgp4" 2>nul
if errorlevel 1 (
    echo.
    echo Dependencies not installed. Installing now...
    spaceenv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
)

REM Run the program
echo ========================================
echo Running AstroCleanAI...
echo ========================================
echo.

spaceenv\Scripts\python.exe main.py

echo.
echo ========================================
echo Program completed!
echo ========================================
echo.
echo Results saved to: output/collision_scenario.html
echo.
echo Opening visualization in browser...
if exist "output/collision_scenario.html" (
    start output/collision_scenario.html
) else (
    echo Warning: Output file not found. Check for errors above.
)
echo.
pause
