import json
import os
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '8209185155:AAHWUrMimRj06E18wuRcji8IF8EtPezDGt0')
ADMIN_IDS = [1787324695]

# Simple in-memory storage for demo (in production, use database)
subscribers = []

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def get_random_image():
    """Get random image URL - you'll need to host images somewhere accessible"""
    images = [
        "https://via.placeholder.com/400x300/0066cc/ffffff?text=Let's+Grow+1",
        "https://via.placeholder.com/400x300/00cc66/ffffff?text=Let's+Grow+2",
        "https://via.placeholder.com/400x300/cc6600/ffffff?text=Let's+Grow+3"
    ]
    return random.choice(images)

async def start_command(update: Update, context):
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # Add subscriber
    if chat_id not in subscribers:
        subscribers.append(chat_id)
    
    welcome_message = f"""
🎉 *Welcome to the Lets Grow Bot!* 🚀

Hey {user.first_name}! Great to have you onboard! 👋

🚀 *Start Earning with Let's Grow Bot!*
💎 *Refer Friends & Earn Rewards Together*

🎁 *What you'll get:*
🌅 Daily earning opportunities
🌙 Exclusive reward updates

Ready to start earning? Let's grow! 💎
    """
    
    keyboard = [
        [InlineKeyboardButton("🚀 Start Bot", url="https://t.me/Letssgrowbot/Earn?startapp=ref_3")],
        [InlineKeyboardButton("👥 Community", url="https://t.me/Lets_Grow_official")],
        [InlineKeyboardButton("📞 Contact", url="https://t.me/LetsGrowCS")]
    ]
    
    if is_admin(user.id):
        keyboard.append([InlineKeyboardButton("⚙️ Admin", callback_data="admin")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def settings_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.edit_message_text("❌ Unauthorized access!")
        return
    
    await query.edit_message_text(
        f"⚙️ *Admin Panel*\n\n"
        f"👥 Total Subscribers: {len(subscribers)}\n"
        f"🤖 Bot Status: Running\n"
        f"📅 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        parse_mode=ParseMode.MARKDOWN
    )

# Main webhook handler
async def webhook_handler(request):
    try:
        # Parse the incoming update
        body = await request.json()
        update = Update.de_json(body, None)
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CallbackQueryHandler(settings_callback, pattern="admin"))
        
        # Process the update
        await application.process_update(update)
        
        return {"statusCode": 200, "body": "OK"}
        
    except Exception as e:
        print(f"Error processing update: {e}")
        return {"statusCode": 500, "body": f"Error: {str(e)}"}

# Vercel serverless function entry point
def handler(request):
    import asyncio
    return asyncio.run(webhook_handler(request))