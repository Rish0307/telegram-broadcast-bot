# 🤖 Telegram Broadcast Bot

Complete broadcast system that can send **unlimited messages** to all your subscribers for **FREE**!

## ✨ Features

### 📢 Message Types
- **Text messages** with rich formatting (bold, italic, code)
- **Images & Photos** with captions and buttons
- **Videos & GIFs** with descriptions
- **Documents & Files** (PDFs, DOCs, etc.)
- **Audio files & Voice messages**
- **Polls & Quizzes** for engagement
- **Location sharing**
- **Contact information**
- **Stickers & Animations**

### 🎛️ Controls
- **Inline keyboards** with custom buttons
- **Web links** and deep links
- **Callback buttons** for interactions
- **Custom reply keyboards**

### 📊 Management
- **Auto subscriber management**
- **Delivery statistics**
- **Failed delivery handling**
- **Blocked user cleanup**
- **Admin controls**

## 🚀 Quick Start

### 1. Get Bot Token
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Create new bot with `/newbot`
3. Copy your bot token
4. **Already done**: `8209185155:AAHWUrMimRj06E18wuRcji8IF8EtPezDGt0`

### 2. Install Dependencies
Run the setup script:
```bash
setup.bat
```

Or manually:
```bash
# Activate your virtual environment
call "C:\Users\HP\OneDrive\Desktop\Ai bot\venv\Scripts\activate.bat"

# Install packages
pip install python-telegram-bot==20.7
pip install python-dotenv==1.0.0
pip install aiofiles==23.2.1
```

### 3. Run the Bot
```bash
python telegram_broadcast_bot.py
```

## 📋 Commands

### User Commands
- `/start` - Subscribe to broadcasts
- `/stop` - Unsubscribe from broadcasts
- `/status` - Check subscription status
- `/help` - Show help message

### Admin Commands
- `/broadcast <message>` - Send text broadcast
- `/broadcastimg` - Reply to image to broadcast it
- `/stats` - View bot statistics

## 💡 Usage Examples

### Simple Text Broadcast
```
/broadcast Hello everyone! This is a test message.
```

### Formatted Text with Buttons
The bot automatically adds:
- ✨ Professional formatting
- 🎯 Inline buttons (Like, Comment, Share)
- ⏰ Timestamp
- 🤖 Branding

### Image Broadcast
1. Send an image to the bot
2. Reply to that image with `/broadcastimg`
3. Image gets sent to all subscribers

## 🎯 Advanced Features

### Rich Text Formatting
```python
message = """
🚀 *EXCITING NEWS!* 

🎯 We're launching something *BIG*!

📝 *Features:*
• ✅ Feature 1: Amazing functionality
• ✅ Feature 2: Super fast performance  
• ✅ Feature 3: Beautiful design

🔗 [Visit Website](https://example.com)
💡 _Stay tuned for more updates!_
`Use code: LAUNCH2024 for discount`
"""
```

### Custom Buttons
```python
keyboard = [
    [InlineKeyboardButton("🌟 Get Started", url="https://example.com")],
    [InlineKeyboardButton("📞 Contact", callback_data="contact"),
     InlineKeyboardButton("ℹ️ Info", callback_data="info")]
]
```

### Polls & Surveys
```python
question = "🗳️ What feature would you like next?"
options = ["🚀 Dark Mode", "📊 Analytics", "🔔 Notifications"]
```

## 📊 Statistics Dashboard

The bot tracks:
- 👥 **Total subscribers**
- ✅ **Successful deliveries**
- ❌ **Failed deliveries**
- 🚫 **Blocked users** (auto-removed)
- 📈 **Engagement rates**

## 🔧 File Structure

```
Broadcast/
├── telegram_broadcast_bot.py      # Main bot file
├── advanced_broadcast_examples.py # Advanced examples
├── .env                          # Bot token (secure)
├── subscribers.json              # Auto-generated subscriber list
├── setup.bat                     # Easy setup script
└── README.md                     # This file
```

## 🎛️ Configuration

### Environment Variables (.env)
```
BOT_TOKEN=8209185155:AAHWUrMimRj06E18wuRcji8IF8EtPezDGt0
```

### Subscriber Management
- Automatically saves to `subscribers.json`
- Auto-removes blocked/deleted users
- Handles rate limiting
- Prevents duplicate subscriptions

## 🚀 Advanced Usage

### Send Different Message Types
```python
# Images with buttons
await broadcast_image_with_buttons("image.jpg")

# Videos with captions  
await broadcast_video_message("video.mp4")

# Documents/files
await broadcast_document("document.pdf", "Important Info")

# Polls for engagement
await broadcast_poll()

# Location sharing
await broadcast_location()

# Audio messages
await broadcast_audio_message("podcast.mp3")
```

### Bulk Operations
```python
# Send to specific group
specific_users = [123456789, 987654321]

# Send with custom timing
await asyncio.sleep(0.05)  # Rate limiting

# Error handling
try:
    await bot.send_message(chat_id, message)
except Exception as e:
    # Handle blocked users
    remove_subscriber(chat_id)
```

## 💰 Cost & Limits

### ✅ FREE Features
- **Unlimited messages** per day
- **Unlimited subscribers**
- **All message types**
- **File uploads** up to 50MB
- **No monthly fees**

### 📏 Technical Limits
- **30 messages/second** (very high)
- **50MB** max file size
- **4096 characters** per message

## 🔒 Security

- ✅ Bot token stored in `.env` file
- ✅ Automatic blocked user cleanup
- ✅ Rate limiting protection
- ✅ Error handling
- ✅ No admin restrictions (you control everything)

## 📱 How Users Interact

1. **Discovery**: Users find your bot link
2. **Subscribe**: Send `/start` to subscribe
3. **Receive**: Get all your broadcasts automatically
4. **Engage**: Click buttons, respond to polls
5. **Manage**: Use `/stop` to unsubscribe anytime

## 🎯 Use Cases

### Business
- 📢 Product announcements
- 💰 Special offers & discounts
- 📊 Survey & feedback collection
- 📰 News & updates

### Content Creators
- 🎥 New video notifications
- 📝 Blog post alerts
- 🎭 Event announcements
- 🎁 Exclusive content sharing

### Communities
- 📅 Event reminders
- 🗳️ Voting & polls
- 📋 Important announcements
- 🤝 Member updates

## 🆘 Support & Troubleshooting

### Common Issues
1. **Bot not responding**: Check token in `.env` file
2. **Can't send messages**: Ensure bot is started with `/start`
3. **Images not sending**: Check file path and size (<50MB)
4. **Rate limiting**: Bot handles this automatically

### Getting Help
- 📚 Check `advanced_broadcast_examples.py` for examples
- 🐛 Check console logs for error messages
- 📖 Read [Telegram Bot API docs](https://core.telegram.org/bots/api)

## 🚀 Next Steps

1. **Run the bot**: `python telegram_broadcast_bot.py`
2. **Test it**: Send yourself `/start` 
3. **Send broadcast**: Use `/broadcast Your message here`
4. **Add subscribers**: Share your bot link
5. **Scale up**: Add more advanced features

---

## 🎉 Ready to Broadcast!

Your bot can now send **unlimited messages** to **unlimited users** for **FREE**! 

**Bot Link**: `https://t.me/YourBotUsername` (Replace with your actual bot username)

**Start broadcasting now**: `python telegram_broadcast_bot.py`