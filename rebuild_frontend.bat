@echo off
echo Rebuilding frontend...
cd frontend
call npm run build
echo.
echo Frontend rebuilt successfully!
echo Refresh your browser to see changes.
pause
