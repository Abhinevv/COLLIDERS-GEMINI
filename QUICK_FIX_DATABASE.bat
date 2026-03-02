@echo off
echo ========================================
echo QUICK DATABASE FIX
echo ========================================
echo.
echo This will populate your database with satellites and show counts.
echo.
pause

call spaceenv\Scripts\activate.bat
python quick_populate.py

echo.
echo ========================================
echo DONE! Now refresh your browser.
echo ========================================
pause
