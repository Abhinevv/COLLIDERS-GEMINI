@echo off
echo ========================================
echo Adding LEO Debris with Space-Track
echo ========================================
echo.

REM Set Space-Track credentials
set SPACETRACK_USER=RIDDHESHMORANKAR53@GMAIL.COM
set SPACETRACK_PASS=QWERTYuiop12345678901234567890

echo Credentials set
echo.

echo Activating virtual environment...
call spaceenv\Scripts\activate.bat

echo.
echo Running add_leo_debris.py...
echo.
python add_leo_debris.py

echo.
echo ========================================
echo Done!
echo ========================================
pause
