@echo off
echo 🚀 Setting up Telegram Broadcast Bot...
echo.

echo 📦 Activating virtual environment...
call "C:\Users\HP\OneDrive\Desktop\Ai bot\venv\Scripts\activate.bat"

echo 📥 Installing required packages...
pip install python-telegram-bot==20.7
pip install python-dotenv==1.0.0
pip install aiofiles==23.2.1

echo.
echo ✅ Setup complete!
echo.
echo 🤖 To run the bot:
echo python telegram_broadcast_bot.py
echo.
echo 📋 Commands available:
echo /start - Subscribe to broadcasts
echo /broadcast [message] - Send broadcast (admin)
echo /stats - View statistics
echo.
pause