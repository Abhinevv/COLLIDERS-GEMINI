@echo off
echo ========================================
echo Adding Satellites with Space-Track
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
echo Running add_satellites_direct.py...
echo.
python add_satellites_direct.py

echo.
echo ========================================
echo Done!
echo ========================================
pause
