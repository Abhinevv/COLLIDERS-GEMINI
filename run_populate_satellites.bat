@echo off
echo ========================================
echo Populating Satellites from TLE Files
echo ========================================
echo.

echo Activating virtual environment...
call spaceenv\Scripts\activate.bat

echo.
echo Running populate_satellites_from_files.py...
echo.
python populate_satellites_from_files.py

echo.
echo ========================================
echo Done!
echo ========================================
pause
