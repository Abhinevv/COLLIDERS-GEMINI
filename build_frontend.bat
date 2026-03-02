@echo off
echo Building AstroCleanAI Frontend...
cd frontend
call npm run build
cd ..
echo.
echo Build complete! Restart the server to use the new version.
pause
