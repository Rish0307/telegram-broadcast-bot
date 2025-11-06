@echo off
echo Installing Python and running Telegram Bot...

REM Install Python using winget
echo Installing Python...
winget install Python.Python.3.11

REM Wait for installation
timeout /t 10 /nobreak >nul

REM Refresh PATH
call refreshenv

REM Install requirements
echo Installing bot dependencies...
pip install -r requirements.txt

REM Run the bot
echo Starting Telegram Bot...
python scheduled_broadcast_bot.py

pause