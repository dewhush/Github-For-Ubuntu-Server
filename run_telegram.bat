@echo off
echo.
echo ========================================
echo   GitHub Followers Bot - Telegram Mode
echo   Created by: dewhush
echo ========================================
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate
) else (
    echo Note: No virtual environment found. Using system Python.
)

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt --quiet

echo.
echo Starting Telegram Bot...
echo.

python telegram_bot.py

pause
