@echo off
REM Refresh TLE data and run AstroCleanAI
REM Double-click this file or run from terminal

echo ========================================
echo Refreshing TLE Data and Running Program
echo ========================================
echo.

REM Delete old TLE files
echo Step 1: Deleting old TLE files...
if exist "data\*.txt" (
    del /q data\*.txt
    echo   ✓ Old TLE files deleted
) else (
    echo   ✓ No old files to delete
)
echo.

REM Download fresh TLE data
echo Step 2: Downloading fresh TLE data...
spaceenv\Scripts\python.exe fetch_tle.py
echo.

REM Run the program
echo Step 3: Running AstroCleanAI...
echo.
spaceenv\Scripts\python.exe main.py
echo.

echo ========================================
echo Done!
echo ========================================
echo.
pause
