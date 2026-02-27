@echo off
REM Batch script to activate virtual environment (works in Command Prompt)
REM This bypasses PowerShell execution policy issues

if exist "spaceenv\Scripts\activate.bat" (
    call spaceenv\Scripts\activate.bat
    echo Virtual environment activated!
    echo.
    echo You can now run:
    echo   pip install -r requirements.txt
    echo   python main.py
) else (
    echo Error: Virtual environment not found!
    echo Please create it first: python -m venv spaceenv
    pause
)
