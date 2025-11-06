import asyncio
import json
import logging
import os
import random
from datetime import datetime, time, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv
import schedule
import threading

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
import telegram

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ScheduledTelegramBot:
    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN')
        self.subscribers_file = 'subscribers.json'
        self.schedule_file = 'broadcast_schedule.json'
        self.messages_file = 'scheduled_messages.json'
        self.subscribers = self.load_subscribers()
        self.scheduled_messages = self.load_scheduled_messages()
        self.application = None
        # ADD YOUR TELEGRAM USER ID HERE FOR ADMIN ACCESS
        self.admin_ids = [1787324695]  # Replace with your actual Telegram user ID
        self.images_folder = 'images'
        
        # Conversation states for broadcast creation
        self.broadcast_states = {}
        self.temp_broadcast_data = {}
        self.one_time_broadcasts = []  # List to store one-time scheduled broadcasts
        
    def load_subscribers(self) -> List[int]:
        """Load subscribers from file"""
        try:
            with open(self.subscribers_file, 'r') as f:
                data = json.load(f)
                return data.get('subscribers', [])
        except FileNotFoundError:
            return []
    
    def load_scheduled_messages(self) -> List[Dict]:
        """Load scheduled messages from file"""
        try:
            with open(self.messages_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return [
                {
                    "id": 1,
                    "time": "09:00",
                    "message": "🌅 Good Morning! Start your day with positivity!",
                    "active": True,
                    "type": "daily"
                },
                {
                    "id": 2,
                    "time": "18:00", 
                    "message": "🌙 Good Evening! Hope you had a productive day!",
                    "active": True,
                    "type": "daily"
                }
            ]
    
    def save_subscribers(self):
        """Save subscribers to file"""
        data = {
            'subscribers': self.subscribers,
            'total_count': len(self.subscribers),
            'last_updated': datetime.now().isoformat()
        }
        with open(self.subscribers_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def save_scheduled_messages(self):
        """Save scheduled messages to file"""
        with open(self.messages_file, 'w') as f:
            json.dump(self.scheduled_messages, f, indent=2)
    
    def add_subscriber(self, chat_id: int) -> bool:
        """Add new subscriber"""
        if chat_id not in self.subscribers:
            self.subscribers.append(chat_id)
            self.save_subscribers()
            logger.info(f"New subscriber added: {chat_id}")
            return True
        return False
    
    def remove_subscriber(self, chat_id: int) -> bool:
        """Remove subscriber"""
        if chat_id in self.subscribers:
            self.subscribers.remove(chat_id)
            self.save_subscribers()
            logger.info(f"Subscriber removed: {chat_id}")
            return True
        return False
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.admin_ids
    
    def get_random_image(self) -> str:
        """Get random image from images folder"""
        try:
            image_files = [f for f in os.listdir(self.images_folder) 
                          if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
            if image_files:
                return os.path.join(self.images_folder, random.choice(image_files))
        except FileNotFoundError:
            pass
        return None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        chat_id = update.effective_chat.id
        user = update.effective_user
        
        is_new = self.add_subscriber(chat_id)
        
        # Get random welcome image
        welcome_image = self.get_random_image()
        
        # Create different welcome messages for admin vs regular users
        if self.is_admin(user.id):
            welcome_message = f"""
🎉 *Welcome to the Lets Grow Bot!* 🚀

Hey {user.first_name}! Great to have you onboard! 👋

🚀 *Start Earning with Let's Grow Bot!*
💎 *Refer Friends & Earn Rewards Together*

👑 *Admin Dashboard:*
📊 *Total Subscribers:* {len(self.subscribers)}

⏰ *Current Schedule:*
🌅 Daily earning opportunities: 09:00 AM
🌙 Exclusive reward updates: 06:00 PM
📊 Weekly summaries: Sunday 10:00 AM
📈 Monthly reports: 1st of month

Ready to start earning? Let's grow! 💎
            """
        else:
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
        
        # Create buttons based on user type (admin gets extra Settings button)
        if self.is_admin(user.id):
            keyboard = [
                [InlineKeyboardButton("🚀 Start Bot", url="https://t.me/Letssgrowbot/Earn")],
                [InlineKeyboardButton("👥 Community", url="https://t.me/Lets_Grow_official")],
                [InlineKeyboardButton("📞 Contact", url="https://t.me/LetsGrowCS")],
                [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("🚀 Start Bot", url="https://t.me/Letssgrowbot/Earn?startapp=ref_3")],
                [InlineKeyboardButton("👥 Community", url="https://t.me/Lets_Grow_official")],
                [InlineKeyboardButton("📞 Contact", url="https://t.me/LetsGrowCS")]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            if welcome_image and os.path.exists(welcome_image):
                # Check file size (skip if too large)
                file_size = os.path.getsize(welcome_image)
                if file_size < 10 * 1024 * 1024:  # Less than 10MB
                    with open(welcome_image, 'rb') as photo:
                        await update.message.reply_photo(
                            photo=photo,
                            caption=welcome_message,
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=reply_markup
                        )
                    return
        except Exception as e:
            logger.warning(f"Failed to send image: {e}")
        
        # Fallback to text message
        await update.message.reply_text(
            welcome_message, 
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def schedule_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current broadcast schedule"""
        user_id = update.effective_user.id
        
        if self.is_admin(user_id):
            # Admin view with detailed information
            schedule_text = "📅 *Current Broadcast Schedule:*\n\n"
            
            for msg in self.scheduled_messages:
                status = "✅" if msg['active'] else "❌"
                schedule_text += f"{status} *{msg['time']}* - {msg['type'].title()}\n"
                schedule_text += f"   📝 {msg['message'][:50]}{'...' if len(msg['message']) > 50 else ''}\n\n"
            
            schedule_text += "\n📊 *Admin Statistics:*\n"
            schedule_text += f"👥 Total Subscribers: {len(self.subscribers)}\n"
            schedule_text += f"⏰ Active Schedules: {len([m for m in self.scheduled_messages if m['active']])}\n"
            schedule_text += f"🕒 Next Broadcast: {self.get_next_broadcast_time()}"
            
            keyboard = [
                [InlineKeyboardButton("➕ Add Schedule", callback_data="add_schedule")],
                [InlineKeyboardButton("⚙️ Manage", callback_data="manage_schedule")]
            ]
        else:
            # Regular user view with general schedule info only
            schedule_text = "📅 *Broadcast Schedule:*\n\n"
            schedule_text += "🌅 *Morning:* 09:00 AM - Daily earning opportunities\n"
            schedule_text += "🌙 *Evening:* 06:00 PM - Exclusive reward updates\n"
            schedule_text += "📊 *Weekly:* Sunday 10:00 AM - Weekly summaries\n"
            schedule_text += "📈 *Monthly:* 1st of month - Monthly reports\n\n"
            schedule_text += "🔔 Stay subscribed to receive all updates automatically!"
            
            keyboard = [
                [InlineKeyboardButton("🚀 Start Bot", url="https://t.me/Letssgrowbot/Earn")],
                [InlineKeyboardButton("👥 Community", url="https://t.me/Lets_Grow_official")],
                [InlineKeyboardButton("📞 Contact", url="https://t.me/LetsGrowCS")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            schedule_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    def get_next_broadcast_time(self) -> str:
        """Get next scheduled broadcast time"""
        now = datetime.now()
        today_times = []
        
        for msg in self.scheduled_messages:
            if msg['active']:
                time_parts = msg['time'].split(':')
                broadcast_time = now.replace(hour=int(time_parts[0]), minute=int(time_parts[1]), second=0, microsecond=0)
                
                if broadcast_time <= now:
                    broadcast_time += timedelta(days=1)
                
                today_times.append(broadcast_time)
        
        if today_times:
            next_time = min(today_times)
            return next_time.strftime('%Y-%m-%d %H:%M')
        return "Not scheduled"
    
    async def broadcast_to_all(self, message: str, message_type: str = "scheduled") -> Dict[str, int]:
        """Broadcast message to all subscribers"""
        success_count = 0
        failed_count = 0
        blocked_users = []
        
        # Add scheduling info to message
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = f"""
{message}

🤖 *Scheduled Broadcast*
🕒 {timestamp}
        """
        
        # Create buttons with your links
        keyboard = [
            [InlineKeyboardButton("🚀 Start Bot", url="https://t.me/Letssgrowbot/Earn?startapp=ref_3")],
            [InlineKeyboardButton("👥 Community", url="https://t.me/Lets_Grow_official")],
            [InlineKeyboardButton("📞 Contact", url="https://t.me/LetsGrowCS")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        for chat_id in self.subscribers.copy():
            try:
                await self.application.bot.send_message(
                    chat_id=chat_id,
                    text=formatted_message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
                success_count += 1
                await asyncio.sleep(0.05)  # Rate limiting
                
            except Exception as e:
                failed_count += 1
                blocked_users.append(chat_id)
                if "blocked" in str(e).lower() or "not found" in str(e).lower():
                    self.remove_subscriber(chat_id)
                logger.warning(f"Failed to send to {chat_id}: {e}")
        
        # Log broadcast results
        logger.info(f"Broadcast complete: {success_count} sent, {failed_count} failed")
        
        return {
            'success': success_count,
            'failed': failed_count,
            'blocked_removed': len(blocked_users)
        }
    
    def setup_scheduler(self):
        """Setup scheduled broadcasts"""
        for msg in self.scheduled_messages:
            if msg['active']:
                if msg['type'] == 'daily':
                    schedule.every().day.at(msg['time']).do(
                        self.run_scheduled_broadcast, 
                        msg['message']
                    )
                    logger.info(f"Scheduled daily broadcast at {msg['time']}")
        
        # Setup weekly summary (every Sunday at 10:00)
        schedule.every().sunday.at("10:00").do(
            self.run_scheduled_broadcast,
            self.get_weekly_summary_message()
        )
        
        # Setup monthly stats (1st of month at 09:00)  
        schedule.every().day.at("09:00").do(self.check_monthly_broadcast)
    
    def run_scheduled_broadcast(self, message: str):
        """Run scheduled broadcast in async context"""
        if self.application:
            asyncio.create_task(self.broadcast_to_all(message, "scheduled"))
    
    def check_monthly_broadcast(self):
        """Check if today is first of month for monthly broadcast"""
        if datetime.now().day == 1:
            monthly_message = f"""
📊 *Monthly Report - {datetime.now().strftime('%B %Y')}*

🎉 Thank you for being part of our community!

📈 *This Month's Highlights:*
• 👥 Total Subscribers: {len(self.subscribers)}
• 📅 Daily broadcasts delivered
• 🚀 New features added

💡 *Coming Next Month:*
• More exciting content
• Interactive features
• Special announcements

Stay tuned for amazing updates! 🌟
            """
            self.run_scheduled_broadcast(monthly_message)
    
    def get_weekly_summary_message(self) -> str:
        """Generate weekly summary message"""
        return f"""
📊 *Weekly Summary - {datetime.now().strftime('%B %d, %Y')}*

🎉 Another great week with our community!

📈 *This Week's Stats:*
• 👥 Active Subscribers: {len(self.subscribers)}
• 📅 Broadcasts Sent: 14 (Daily morning & evening)
• 🚀 Engagement: High

💡 *Week Ahead:*
• Continued daily updates
• Special announcements
• New features coming

Have a wonderful week ahead! 🌟
        """
    
    async def add_schedule_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add new scheduled broadcast (Admin only)"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text(
                "❌ *Access Denied*\n\nOnly bot admin can add schedules.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "Usage: /addschedule <time> <message>\n"
                "Example: /addschedule 15:30 Afternoon motivation message!"
            )
            return
        
        time_str = context.args[0]
        message = " ".join(context.args[1:])
        
        try:
            # Validate time format
            time.fromisoformat(time_str + ":00")
            
            new_schedule = {
                "id": len(self.scheduled_messages) + 1,
                "time": time_str,
                "message": message,
                "active": True,
                "type": "daily"
            }
            
            self.scheduled_messages.append(new_schedule)
            self.save_scheduled_messages()
            
            # Add to scheduler
            schedule.every().day.at(time_str).do(
                self.run_scheduled_broadcast, 
                message
            )
            
            await update.message.reply_text(
                f"✅ *Schedule Added Successfully!*\n\n"
                f"⏰ Time: {time_str}\n"
                f"📝 Message: {message[:100]}{'...' if len(message) > 100 else ''}\n"
                f"📅 Type: Daily\n"
                f"✅ Status: Active",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid time format! Use HH:MM (24-hour format)\n"
                "Example: 09:30 or 15:45"
            )
    
    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manual broadcast command (Admin only)"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text(
                "❌ *Access Denied*\n\nOnly bot admin can send broadcasts.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /broadcast <your message>")
            return
        
        message = " ".join(context.args)
        await update.message.reply_text("📤 Starting broadcast...")
        
        results = await self.broadcast_to_all(message, "manual")
        
        result_message = f"""
✅ *Manual Broadcast Complete!*

📊 *Results:*
✅ Successfully sent: {results['success']}
❌ Failed: {results['failed']}
🚫 Blocked users removed: {results['blocked_removed']}
👥 Total active subscribers: {len(self.subscribers)}
        """
        
        await update.message.reply_text(result_message, parse_mode=ParseMode.MARKDOWN)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show detailed statistics (Admin only)"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text(
                "❌ *Access Denied*\n\nOnly bot admin can view detailed statistics.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        active_schedules = len([m for m in self.scheduled_messages if m['active']])
        next_broadcast = self.get_next_broadcast_time()
        
        stats_message = f"""
📊 *Admin Statistics Dashboard*

👥 *Subscribers:*
• Total: {len(self.subscribers)}
• Active: {len(self.subscribers)}
• Growth: +New subscribers daily

⏰ *Scheduling:*
• Active Schedules: {active_schedules}
• Total Schedules: {len(self.scheduled_messages)}
• Next Broadcast: {next_broadcast}

📈 *Broadcasts Today:*
• Scheduled: Auto-sent at set times
• Manual: Available anytime
• Success Rate: ~95%+ delivery

🤖 *Bot Status:*
• Status: Active 24/7
• Uptime: Running continuously
• Features: All operational

📅 *Schedule Overview:*
        """
        
        for msg in self.scheduled_messages:
            if msg['active']:
                stats_message += f"• {msg['time']} - Daily broadcast\n"
        
        await update.message.reply_text(stats_message, parse_mode=ParseMode.MARKDOWN)
    
    def run_scheduler(self):
        """Run scheduler in separate thread"""
        while True:
            schedule.run_pending()
            # Check for one-time broadcasts
            self.check_one_time_broadcasts()
            threading.Event().wait(30)  # Check every 30 seconds
    
    def check_one_time_broadcasts(self):
        """Check and execute one-time broadcasts"""
        if not hasattr(self, 'one_time_broadcasts'):
            return
        
        # Use UTC time for consistency
        now = datetime.utcnow()
        broadcasts_to_remove = []
        
        for i, broadcast in enumerate(self.one_time_broadcasts):
            target_time = broadcast['datetime']
            
            # Debug output
            time_diff = (target_time - now).total_seconds()
            if abs(time_diff) <= 120:  # Only show debug for broadcasts within 2 minutes
                print(f"DEBUG: One-time broadcast check - Target: {target_time}, Now: {now}, Diff: {time_diff}s")
            
            # Check if it's time to send (within 2 minute window for safety)
            if now >= target_time and now <= target_time + timedelta(minutes=2):
                print(f"Executing one-time broadcast scheduled for {target_time}")
                # Execute the broadcast using the existing method
                if self.application:
                    # Schedule the broadcast using the same pattern as regular scheduled broadcasts
                    import threading
                    broadcast_thread = threading.Thread(
                        target=self.run_one_time_broadcast_sync,
                        args=(broadcast,)
                    )
                    broadcast_thread.start()
                broadcasts_to_remove.append(i)
            # Remove broadcasts that are more than 1 hour past due
            elif now > target_time + timedelta(hours=1):
                print(f"Removing expired one-time broadcast: {target_time}")
                broadcasts_to_remove.append(i)
        
        # Remove executed/expired broadcasts
        for i in reversed(broadcasts_to_remove):
            del self.one_time_broadcasts[i]
    
    async def send_one_time_broadcast(self, broadcast_data):
        """Send one-time scheduled broadcast"""
        print(f"Sending one-time broadcast: {broadcast_data['message'][:50]}...")
        
        # Create keyboard
        keyboard = []
        for button in broadcast_data.get('buttons', []):
            if 'url' in button:
                keyboard.append([InlineKeyboardButton(button['text'], url=button['url'])])
            else:
                keyboard.append([InlineKeyboardButton(button['text'], callback_data=button['callback_data'])])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        success_count = 0
        failed_count = 0
        
        for chat_id in self.subscribers.copy():
            try:
                if broadcast_data.get('image') and os.path.exists(broadcast_data['image']):
                    with open(broadcast_data['image'], 'rb') as photo:
                        await self.application.bot.send_photo(
                            chat_id=chat_id,
                            photo=photo,
                            caption=broadcast_data['message'],
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=reply_markup
                        )
                else:
                    await self.application.bot.send_message(
                        chat_id=chat_id,
                        text=broadcast_data['message'],
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=reply_markup
                    )
                success_count += 1
                await asyncio.sleep(0.05)
                
            except Exception as e:
                failed_count += 1
                if "blocked" in str(e).lower() or "not found" in str(e).lower():
                    self.remove_subscriber(chat_id)
                logger.warning(f"Failed to send one-time broadcast to {chat_id}: {e}")
        
        logger.info(f"One-time broadcast sent: {success_count} success, {failed_count} failed")
        print(f"One-time broadcast completed: {success_count} sent, {failed_count} failed")
    
    def run_one_time_broadcast_sync(self, broadcast_data):
        """Run one-time broadcast in sync context (for threading)"""
        try:
            # Create a simple broadcast message
            message = broadcast_data['message']
            
            # Add timestamp to message
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            formatted_message = f"""
{message}

🤖 *One-time Broadcast*
🕒 {timestamp}
            """
            
            # Create keyboard
            keyboard_data = []
            for button in broadcast_data.get('buttons', []):
                if 'url' in button:
                    keyboard_data.append({'text': button['text'], 'url': button['url']})
                else:
                    keyboard_data.append({'text': button['text'], 'callback_data': button['callback_data']})
            
            # Use the existing broadcast method by temporarily storing the data
            temp_data = {
                'message': formatted_message,
                'image': broadcast_data.get('image'),
                'buttons': keyboard_data
            }
            
            # Send using asyncio in a new event loop
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.send_one_time_broadcast(broadcast_data))
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error in one-time broadcast: {e}")
            print(f"Error in one-time broadcast: {e}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help message"""
        help_text = """
🤖 *Let's Grow Bot Help*

*User Commands:*
/start - Subscribe to earning updates
/stop - Unsubscribe from updates
/schedule - View earning schedule
/help - Show this help

*Admin Commands:*
/broadcast <message> - Send immediate broadcast
/addschedule <time> <message> - Add scheduled broadcast
/stats - View detailed statistics

*Features:*
⏰ Daily earning opportunities
📅 Weekly earning summaries
📊 Monthly reward reports
📱 Manual broadcasts
🎯 Auto subscriber management

*Current Schedule:*
🌅 09:00 - Daily earning opportunities
🌙 18:00 - Exclusive reward updates
📊 Sunday 10:00 - Weekly summaries
📈 Monthly 1st 09:00 - Monthly reports

*Examples:*
/broadcast New earning opportunity available!
/addschedule 12:00 Midday reward alert!
        """
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if query.data == "schedule":
            # Show schedule with proper admin restrictions
            if self.is_admin(user_id):
                # Admin view with detailed information
                schedule_text = "📅 *Current Broadcast Schedule:*\n\n"
                
                for msg in self.scheduled_messages:
                    status = "✅" if msg['active'] else "❌"
                    schedule_text += f"{status} *{msg['time']}* - {msg['type'].title()}\n"
                    schedule_text += f"   📝 {msg['message'][:50]}{'...' if len(msg['message']) > 50 else ''}\n\n"
                
                schedule_text += "\n📊 *Admin Statistics:*\n"
                schedule_text += f"👥 Total Subscribers: {len(self.subscribers)}\n"
                schedule_text += f"⏰ Active Schedules: {len([m for m in self.scheduled_messages if m['active']])}\n"
                schedule_text += f"🕒 Next Broadcast: {self.get_next_broadcast_time()}"
            else:
                # Regular user view with general schedule info only
                schedule_text = "📅 *Broadcast Schedule:*\n\n"
                schedule_text += "🌅 *Morning:* 09:00 AM - Daily earning opportunities\n"
                schedule_text += "🌙 *Evening:* 06:00 PM - Exclusive reward updates\n"
                schedule_text += "📊 *Weekly:* Sunday 10:00 AM - Weekly summaries\n"
                schedule_text += "📈 *Monthly:* 1st of month - Monthly reports\n\n"
                schedule_text += "🔔 Stay subscribed to receive all updates automatically!"
            
            try:
                await query.edit_message_text(
                    schedule_text,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                # If edit fails, send new message
                await query.message.reply_text(
                    schedule_text,
                    parse_mode=ParseMode.MARKDOWN
                )
        
        elif query.data == "settings":
            if not self.is_admin(user_id):
                await query.edit_message_text(
                    "❌ *Access Denied*\n\nOnly bot admin can access settings.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            settings_text = f"""
⚙️ *Admin Settings Panel*

👑 *Admin Access Granted*

📊 *Current Status:*
• Total Subscribers: {len(self.subscribers)}
• Active Schedules: {len([m for m in self.scheduled_messages if m['active']])}
• Bot Status: Running

⚡ *Quick Actions:*
Use these commands:

🔹 `/broadcast <message>` - Send immediate broadcast
🔹 `/addschedule <time> <message>` - Add new schedule
🔹 `/stats` - Detailed statistics

💡 *Current Schedules:*
            """
            
            for msg in self.scheduled_messages:
                if msg['active']:
                    settings_text += f"• {msg['time']} - {msg['message'][:30]}...\n"
            
            keyboard = [
                [InlineKeyboardButton("📊 Full Stats", callback_data="admin_stats")],
                [InlineKeyboardButton("🔄 Refresh", callback_data="settings")],
                [InlineKeyboardButton("📝 Set New Broadcast", callback_data="set_new_broadcast"),
                 InlineKeyboardButton("👁️ View Broadcast", callback_data="view_broadcast")],
                [InlineKeyboardButton("✏️ Edit Broadcast", callback_data="edit_broadcast"),
                 InlineKeyboardButton("📅 Daily Broadcast", callback_data="daily_broadcast")],
                [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                await query.edit_message_text(
                    settings_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            except Exception:
                await query.message.reply_text(
                    settings_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
        
        elif query.data == "admin_stats":
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            # Show detailed admin stats
            active_schedules = len([m for m in self.scheduled_messages if m['active']])
            next_broadcast = self.get_next_broadcast_time()
            
            admin_stats = f"""
👑 *Admin Statistics Dashboard*

👥 *Subscribers:*
• Total: {len(self.subscribers)}
• Active: {len(self.subscribers)}
• Latest ID: {max(self.subscribers) if self.subscribers else 'None'}

⏰ *Scheduling:*
• Active: {active_schedules}
• Total: {len(self.scheduled_messages)}
• Next: {next_broadcast}

📈 *Performance:*
• Success Rate: ~95%+
• Auto Cleanup: Enabled
• Rate Limiting: Active

🔧 *System:*
• Status: Online
• Admin Users: {len(self.admin_ids)}
• Files: All operational
            """
            
            keyboard = [
                [InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                await query.edit_message_text(
                    admin_stats,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            except Exception:
                await query.message.reply_text(
                    admin_stats,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
        
        elif query.data == "help":
            help_text = """
🤖 *Scheduled Broadcast Bot Help*

*User Commands:*
/start - Subscribe to scheduled broadcasts
/schedule - View broadcast schedule
/help - Show this help

*Features for Subscribers:*
⏰ Daily scheduled broadcasts
📅 Weekly summaries
📊 Monthly reports
🔔 Instant notifications

*Current Schedule:*
🌅 09:00 - Morning motivation
🌙 18:00 - Evening reflection
📊 Sunday 10:00 - Weekly summary
📈 Monthly 1st - Monthly report

📱 Just stay subscribed and receive all updates automatically!
            """
            
            try:
                await query.edit_message_text(
                    help_text,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                await query.message.reply_text(
                    help_text,
                    parse_mode=ParseMode.MARKDOWN
                )
        
        elif query.data == "set_new_broadcast":
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            # Step 1: Show random image and ask for text
            random_image = self.get_random_image()
            
            # Initialize broadcast data for this user
            self.temp_broadcast_data[user_id] = {
                'image': random_image,
                'text': None,
                'button_count': None,
                'buttons': []
            }
            
            self.broadcast_states[user_id] = 'waiting_for_text'
            
            broadcast_text = """
📝 *Set New Broadcast Message*

🖼️ *Step 1: Image Selected*
Random image has been selected from your images folder.

💬 *Step 2: Enter Your Text*
Please type your broadcast message text and send it.

Example: "🚀 New earning opportunity is here! Start now and earn rewards!"
            """
            
            keyboard = [
                [InlineKeyboardButton("⬅️ Back to Settings", callback_data="cancel_broadcast")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                if random_image and os.path.exists(random_image):
                    with open(random_image, 'rb') as photo:
                        await query.edit_message_media(
                            media=telegram.InputMediaPhoto(
                                media=photo,
                                caption=broadcast_text,
                                parse_mode=ParseMode.MARKDOWN
                            ),
                            reply_markup=reply_markup
                        )
                else:
                    await query.edit_message_text(
                        broadcast_text,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=reply_markup
                    )
            except Exception as e:
                logger.warning(f"Failed to show image: {e}")
                await query.edit_message_text(
                    broadcast_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
        
        elif query.data == "view_broadcast":
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            # Show all scheduled broadcasts
            broadcast_text = "👁️ *View All Broadcast Messages*\n\n"
            
            if not self.scheduled_messages:
                broadcast_text += "❌ No scheduled broadcasts found."
            else:
                # Group broadcasts by type
                daily_broadcasts = [msg for msg in self.scheduled_messages if msg.get('type') in ['daily', 'custom'] and msg.get('active', True)]
                one_time_broadcasts = getattr(self, 'one_time_broadcasts', [])
                
                if daily_broadcasts:
                    broadcast_text += "🔁 *Daily Broadcasts:*\n"
                    for i, msg in enumerate(daily_broadcasts, 1):
                        status = "✅" if msg.get('active', True) else "❌"
                        original_time = msg.get('original_time', f"UTC {msg['time']}")
                        broadcast_text += f"{status} **{i}.** {original_time}\n"
                        broadcast_text += f"   📝 {msg['message'][:60]}{'...' if len(msg['message']) > 60 else ''}\n"
                        if msg.get('buttons'):
                            broadcast_text += f"   🔘 {len(msg['buttons'])} button(s)\n"
                        broadcast_text += "\n"
                
                if one_time_broadcasts:
                    broadcast_text += f"📅 *One-time Broadcasts ({len(one_time_broadcasts)}):*\n"
                    for i, broadcast in enumerate(one_time_broadcasts, 1):
                        target_time = broadcast['datetime']
                        original_time = broadcast.get('original_time', f"UTC {target_time.strftime('%H:%M')}")
                        broadcast_text += f"🕰️ **{i}.** {original_time}\n"
                        broadcast_text += f"   📅 {target_time.strftime('%Y-%m-%d %H:%M')} UTC\n"
                        broadcast_text += f"   📝 {broadcast['message'][:50]}{'...' if len(broadcast['message']) > 50 else ''}\n"
                        if broadcast.get('buttons'):
                            broadcast_text += f"   🔘 {len(broadcast['buttons'])} button(s)\n"
                        broadcast_text += "\n"
                
                # Add summary
                total_daily = len(daily_broadcasts)
                total_onetime = len(one_time_broadcasts)
                broadcast_text += f"\n📊 *Summary:*\n"
                broadcast_text += f"• Daily: {total_daily}\n"
                broadcast_text += f"• One-time: {total_onetime}\n"
                broadcast_text += f"• Total: {total_daily + total_onetime}"
            
            keyboard = [
                [InlineKeyboardButton("🔄 Refresh", callback_data="view_broadcast")],
                [InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                await query.edit_message_text(
                    broadcast_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            except Exception:
                await query.message.reply_text(
                    broadcast_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
        
        elif query.data == "edit_broadcast":
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            # Show editable broadcasts
            await self.show_editable_broadcasts(query, user_id)
        
        elif query.data == "daily_broadcast":
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            # Show daily broadcast management
            await self.show_daily_broadcast_management(query, user_id)
        
        elif query.data == "back_to_menu":
            # Return to main welcome menu
            user = query.from_user
            
            if self.is_admin(user_id):
                welcome_message = f"""
🎉 *Welcome to the Lets Grow Bot!* 🚀

Hey {user.first_name}! Great to have you onboard! 👋

🚀 *Start Earning with Let's Grow Bot!*
💎 *Refer Friends & Earn Rewards Together*

👑 *Admin Dashboard:*
📊 *Total Subscribers:* {len(self.subscribers)}

⏰ *Current Schedule:*
🌅 Daily earning opportunities: 09:00 AM
🌙 Exclusive reward updates: 06:00 PM
📊 Weekly summaries: Sunday 10:00 AM
📈 Monthly reports: 1st of month

Ready to start earning? Let's grow! 💎
                """
                
                keyboard = [
                    [InlineKeyboardButton("🚀 Start Bot", url="https://t.me/Letssgrowbot/Earn")],
                    [InlineKeyboardButton("👥 Community", url="https://t.me/Lets_Grow_official")],
                    [InlineKeyboardButton("📞 Contact", url="https://t.me/LetsGrowCS")],
                    [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
                ]
            else:
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
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                await query.edit_message_text(
                    welcome_message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            except Exception:
                await query.message.reply_text(
                    welcome_message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
        
        elif query.data == "cancel_broadcast":
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            # Clear broadcast state
            if user_id in self.broadcast_states:
                del self.broadcast_states[user_id]
            if user_id in self.temp_broadcast_data:
                del self.temp_broadcast_data[user_id]
            
            # Return to settings
            await self.show_admin_settings(query, user_id)
        
        elif query.data.startswith("button_count_"):
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            button_count = int(query.data.split("_")[2])
            self.temp_broadcast_data[user_id]['button_count'] = button_count
            
            if button_count == 0:
                # No buttons needed, go straight to preview
                await self.show_broadcast_preview_from_callback(query, user_id)
            else:
                # Ask for button details
                self.broadcast_states[user_id] = 'waiting_for_buttons'
                await self.ask_for_button_details(query, user_id, 1)
        
        elif query.data == "frequency_today":
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            # Schedule for today only
            await self.schedule_broadcast_once(query, user_id)
        
        elif query.data == "frequency_daily":
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            # Schedule for daily
            await self.schedule_broadcast_daily(query, user_id)
        
        elif query.data.startswith("edit_broadcast_"):
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            # Extract broadcast ID and show edit options
            broadcast_id = int(query.data.split("_")[2])
            await self.show_broadcast_edit_options(query, user_id, broadcast_id)
        
        elif query.data == "manage_daily_status":
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            # Show status management for daily broadcasts
            await self.show_daily_status_management(query, user_id)
        
        elif query.data.startswith("toggle_status_"):
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            # Toggle broadcast status
            broadcast_id = int(query.data.split("_")[2])
            await self.toggle_broadcast_status(query, user_id, broadcast_id)
        
        elif query.data.startswith("edit_time_"):
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            broadcast_id = int(query.data.split("_")[2])
            # Store the broadcast ID for editing
            self.broadcast_states[user_id] = f'editing_time_{broadcast_id}'
            
            # Find the broadcast
            broadcast = None
            for msg in self.scheduled_messages:
                if msg['id'] == broadcast_id:
                    broadcast = msg
                    break
            
            if not broadcast:
                await query.edit_message_text("❌ Broadcast not found.")
                return
            
            current_time = broadcast.get('original_time', f"UTC {broadcast['time']}")
            
            edit_text = f"""
🕰️ *Edit Broadcast Time*

📋 **Current Time:** {current_time}

🌍 *Enter New Time with Timezone:*
Please enter the new time in timezone format.

🕒 *Format: UTC[+/-offset] HH:MM*
Examples:
• `UTC+5:30 19:48` (India)
• `UTC+6 14:30` (Bangladesh)
• `UTC-5 09:15` (US Eastern)
• `UTC+0 13:45` (London/UTC)

Type your new time:
            """
            
            keyboard = [
                [InlineKeyboardButton("❌ Cancel", callback_data=f"edit_broadcast_{broadcast_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                edit_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        
        elif query.data.startswith("edit_message_"):
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            broadcast_id = int(query.data.split("_")[2])
            # Store the broadcast ID for editing
            self.broadcast_states[user_id] = f'editing_message_{broadcast_id}'
            
            # Find the broadcast
            broadcast = None
            for msg in self.scheduled_messages:
                if msg['id'] == broadcast_id:
                    broadcast = msg
                    break
            
            if not broadcast:
                await query.edit_message_text("❌ Broadcast not found.")
                return
            
            edit_text = f"""
📝 *Edit Broadcast Message*

📋 **Current Message:**
{broadcast['message']}

✏️ *Enter New Message:*
Type your new broadcast message and send it.

📝 You can use markdown formatting (*bold*, _italic_, etc.)
            """
            
            keyboard = [
                [InlineKeyboardButton("❌ Cancel", callback_data=f"edit_broadcast_{broadcast_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                edit_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        
        elif query.data.startswith("edit_buttons_"):
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            broadcast_id = int(query.data.split("_")[2])
            await self.show_edit_buttons_options(query, user_id, broadcast_id)
        
        elif query.data.startswith("delete_broadcast_"):
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            broadcast_id = int(query.data.split("_")[2])
            await self.confirm_delete_broadcast(query, user_id, broadcast_id)
        
        elif query.data.startswith("confirm_delete_"):
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            # Actually delete the broadcast
            broadcast_id = int(query.data.split("_")[2])
            await self.delete_broadcast(query, user_id, broadcast_id)
        
        elif query.data.startswith("clear_buttons_"):
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            broadcast_id = int(query.data.split("_")[2])
            await self.clear_broadcast_buttons(query, user_id, broadcast_id)
        
        elif query.data.startswith("recreate_buttons_"):
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            broadcast_id = int(query.data.split("_")[2])
            await self.start_recreate_buttons(query, user_id, broadcast_id)
        
        elif query.data.startswith("recreate_count_"):
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            # Parse recreate_count_X_broadcastid
            parts = query.data.split("_")
            button_count = int(parts[2])
            broadcast_id = int(parts[3])
            
            # Store the button count and broadcast ID
            if user_id not in self.temp_broadcast_data:
                self.temp_broadcast_data[user_id] = {}
            
            self.temp_broadcast_data[user_id].update({
                'editing_broadcast_id': broadcast_id,
                'button_count': button_count,
                'buttons': []
            })
            
            if button_count == 0:
                # No buttons, apply immediately
                await self.apply_recreated_buttons(query, user_id, broadcast_id, [])
            else:
                # Ask for button details
                self.broadcast_states[user_id] = f'recreating_button_1_{broadcast_id}'
                await self.ask_for_recreate_button_details(query, user_id, 1, button_count, broadcast_id)
        
        elif query.data.startswith("add_button_"):
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            broadcast_id = int(query.data.split("_")[2])
            await self.start_add_single_button(query, user_id, broadcast_id)
        
        elif query.data == "send_now_broadcast":
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            await self.send_broadcast_now(query, user_id)
        
        elif query.data == "schedule_broadcast":
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            self.broadcast_states[user_id] = 'waiting_for_schedule_time'
            
            # Get current UTC time
            utc_now = datetime.now()
            current_utc_time = utc_now.strftime('%H:%M')
            
            schedule_text = f"""
🕰️ *Schedule Broadcast*

🌍 *Step: Set Time with Timezone*
Please enter your timezone and time.

🕒 *Format: UTC[+/-offset] HH:MM*
Examples:
• `UTC+5:30 19:48` (India)
• `UTC+6 19:48` (Bangladesh)
• `UTC-5 14:30` (US Eastern)
• `UTC+0 13:45` (London/UTC)
• `UTC+8 21:00` (China/Singapore)

⏰ *Current UTC Time:* {current_utc_time}

📝 *Your input will be converted to UTC automatically.*

Type your timezone and time:
            """
            
            keyboard = [
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_broadcast")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Handle both text messages and image messages
            try:
                # Try to edit as text message first
                await query.edit_message_text(
                    schedule_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            except Exception as e:
                # If editing fails (likely because it's an image message), send a new message
                if "no text in the message to edit" in str(e).lower():
                    await query.message.reply_text(
                        schedule_text,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=reply_markup
                    )
                else:
                    # For other errors, try to send a new message
                    await query.message.reply_text(
                        schedule_text,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=reply_markup
                    )
        
        elif query.data == "confirm_broadcast":
            if not self.is_admin(user_id):
                await query.edit_message_text("❌ Access Denied")
                return
            
            # Send the broadcast
            data = self.temp_broadcast_data[user_id]
            
            # Create keyboard for broadcast
            keyboard = []
            for button in data['buttons']:
                keyboard.append([InlineKeyboardButton(button['text'], url=button['url'])])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send broadcast to all subscribers
            success_count = 0
            failed_count = 0
            
            for chat_id in self.subscribers.copy():
                try:
                    if data['image'] and os.path.exists(data['image']):
                        with open(data['image'], 'rb') as photo:
                            await self.application.bot.send_photo(
                                chat_id=chat_id,
                                photo=photo,
                                caption=data['text'],
                                parse_mode=ParseMode.MARKDOWN,
                                reply_markup=reply_markup
                            )
                    else:
                        await self.application.bot.send_message(
                            chat_id=chat_id,
                            text=data['text'],
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=reply_markup
                        )
                    success_count += 1
                    await asyncio.sleep(0.05)  # Rate limiting
                    
                except Exception as e:
                    failed_count += 1
                    if "blocked" in str(e).lower() or "not found" in str(e).lower():
                        self.remove_subscriber(chat_id)
                    logger.warning(f"Failed to send broadcast to {chat_id}: {e}")
            
            # Clear broadcast state
            if user_id in self.broadcast_states:
                del self.broadcast_states[user_id]
            if user_id in self.temp_broadcast_data:
                del self.temp_broadcast_data[user_id]
            
            # Show results
            result_text = f"""
✅ *Broadcast Sent Successfully!*

📊 *Results:*
• Successfully sent: {success_count}
• Failed: {failed_count}
• Total subscribers: {len(self.subscribers)}
            """
            
            keyboard = [
                [InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                result_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        
        # Engagement buttons
        elif query.data in ["like", "comment", "share"]:
            reactions = {
                "like": "👍 Thanks for liking!",
                "comment": "💬 Thanks for your engagement!", 
                "share": "📤 Thanks for sharing!"
            }
            await query.answer(reactions.get(query.data, "Thanks!"))
    
    async def show_admin_settings(self, query, user_id):
        """Helper method to show admin settings panel"""
        settings_text = f"""
⚙️ *Admin Settings Panel*

👑 *Admin Access Granted*

📊 *Current Status:*
• Total Subscribers: {len(self.subscribers)}
• Active Schedules: {len([m for m in self.scheduled_messages if m['active']])}
• Bot Status: Running

⚡ *Quick Actions:*
Use these commands:

🔹 `/broadcast <message>` - Send immediate broadcast
🔹 `/addschedule <time> <message>` - Add new schedule
🔹 `/stats` - Detailed statistics

💡 *Current Schedules:*
        """
        
        for msg in self.scheduled_messages:
            if msg['active']:
                settings_text += f"• {msg['time']} - {msg['message'][:30]}...\n"
        
        keyboard = [
            [InlineKeyboardButton("📊 Full Stats", callback_data="admin_stats")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="settings")],
            [InlineKeyboardButton("📝 Set New Broadcast", callback_data="set_new_broadcast"),
             InlineKeyboardButton("👁️ View Broadcast", callback_data="view_broadcast")],
            [InlineKeyboardButton("✏️ Edit Broadcast", callback_data="edit_broadcast"),
             InlineKeyboardButton("📅 Daily Broadcast", callback_data="daily_broadcast")],
            [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                settings_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception:
            await query.message.reply_text(
                settings_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def ask_for_button_count(self, update, user_id):
        """Ask user how many buttons they want"""
        button_text = """
📝 *Set New Broadcast Message*

🔘 *Step 3: Choose Button Count*
How many buttons do you want below your message?

Select 1, 2, or 3 buttons:
        """
        
        keyboard = [
            [InlineKeyboardButton("❌ No Button", callback_data="button_count_0")],
            [InlineKeyboardButton("1️⃣ One Button", callback_data="button_count_1")],
            [InlineKeyboardButton("2️⃣ Two Buttons", callback_data="button_count_2")],
            [InlineKeyboardButton("3️⃣ Three Buttons", callback_data="button_count_3")],
            [InlineKeyboardButton("⬅️ Back to Settings", callback_data="cancel_broadcast")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.reply_text(
            button_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def ask_for_button_details(self, query, user_id, button_num):
        """Ask for button text and link (for callback queries)"""
        button_count = self.temp_broadcast_data[user_id]['button_count']
        
        button_text = f"""
📝 *Set New Broadcast Message*

🔘 *Step 4: Button {button_num}/{button_count}*
Please provide button text and action for Button {button_num}:

🔗 *For URL Button:*
Format: ButtonText | https://your-link.com
Example: Start Earning | https://t.me/Letssgrowbot/Earn

💬 *For Text Response Button:*
Format: ButtonText | TEXT
Example: Get Help | TEXT

Type your response and send it.
        """
        
        self.broadcast_states[user_id] = f'waiting_for_button_{button_num}'
        
        keyboard = [
            [InlineKeyboardButton("⬅️ Back to Settings", callback_data="cancel_broadcast")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                button_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception:
            await query.message.reply_text(
                button_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def ask_for_next_button(self, message, user_id, button_num):
        """Ask for button text and link (for regular messages)"""
        button_count = self.temp_broadcast_data[user_id]['button_count']
        
        button_text = f"""
📝 *Set New Broadcast Message*

🔘 *Step 4: Button {button_num}/{button_count}*
Please provide button text and action for Button {button_num}:

🔗 *For URL Button:*
Format: ButtonText | https://your-link.com
Example: Start Earning | https://t.me/Letssgrowbot/Earn

💬 *For Text Response Button:*
Format: ButtonText | TEXT
Example: Get Help | TEXT

Type your response and send it.
        """
        
        self.broadcast_states[user_id] = f'waiting_for_button_{button_num}'
        
        keyboard = [
            [InlineKeyboardButton("⬅️ Back to Settings", callback_data="cancel_broadcast")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            button_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def ask_broadcast_frequency(self, message, user_id):
        """Ask user to choose broadcast frequency"""
        data = self.temp_broadcast_data[user_id]
        
        frequency_text = f"""
🕰️ *Schedule Broadcast*

✅ *Time Set Successfully!*
• Original: {data['original_time']}
• UTC Equivalent: {data['schedule_time']}

📅 *Choose Frequency:*
When do you want this broadcast to be sent?
        """
        
        keyboard = [
            [InlineKeyboardButton("📅 Today Only", callback_data="frequency_today")],
            [InlineKeyboardButton("🔁 Daily", callback_data="frequency_daily")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_broadcast")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            frequency_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
            )
    
    async def show_broadcast_preview_from_callback(self, query, user_id):
        """Show broadcast preview from callback query"""
        data = self.temp_broadcast_data[user_id]
        
        preview_text = f"""
🔍 *Broadcast Preview*

{data['text']}

📊 *Statistics:*
• Will be sent to: {len(self.subscribers)} subscribers
• Buttons: {len(data['buttons'])}
        """
        
        # Create preview buttons (if any)
        keyboard = []
        for button in data['buttons']:
            if 'url' in button:
                keyboard.append([InlineKeyboardButton(button['text'], url=button['url'])])
            else:
                keyboard.append([InlineKeyboardButton(button['text'], callback_data=button['callback_data'])])
        
        # Add control buttons
        keyboard.extend([
            [InlineKeyboardButton("🚀 Send Now", callback_data="send_now_broadcast"),
             InlineKeyboardButton("🕰️ Schedule", callback_data="schedule_broadcast")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_broadcast")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send preview with image if available
        try:
            if data['image'] and os.path.exists(data['image']):
                with open(data['image'], 'rb') as photo:
                    await query.edit_message_media(
                        media=telegram.InputMediaPhoto(
                            media=photo,
                            caption=preview_text,
                            parse_mode=ParseMode.MARKDOWN
                        ),
                        reply_markup=reply_markup
                    )
            else:
                await query.edit_message_text(
                    preview_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
        except Exception as e:
            logger.warning(f"Failed to show preview: {e}")
            await query.message.reply_text(
                preview_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def show_editable_broadcasts(self, query, user_id):
        """Show list of broadcasts that can be edited"""
        broadcast_text = "✏️ *Edit Broadcast Messages*\n\n"
        
        # Get editable broadcasts (daily/custom only)
        editable_broadcasts = [msg for msg in self.scheduled_messages if msg.get('type') in ['daily', 'custom']]
        
        if not editable_broadcasts:
            broadcast_text += "❌ No editable broadcasts found.\n\n"
            broadcast_text += "You can only edit daily/custom broadcasts."
        else:
            broadcast_text += "Select a broadcast to edit:\n\n"
            
            for i, msg in enumerate(editable_broadcasts):
                status = "✅" if msg.get('active', True) else "❌"
                original_time = msg.get('original_time', f"UTC {msg['time']}")
                broadcast_text += f"{status} **{i+1}.** {original_time}\n"
                broadcast_text += f"   📝 {msg['message'][:50]}{'...' if len(msg['message']) > 50 else ''}\n\n"
        
        # Create buttons for each editable broadcast
        keyboard = []
        for i, msg in enumerate(editable_broadcasts):
            button_text = f"{i+1}. {msg.get('original_time', msg['time'])}"
            if len(button_text) > 30:
                button_text = button_text[:27] + "..."
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"edit_broadcast_{msg['id']}")])
        
        keyboard.append([InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                broadcast_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception:
            await query.message.reply_text(
                broadcast_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def show_broadcast_edit_options(self, query, user_id, broadcast_id):
        """Show edit options for a specific broadcast"""
        # Find the broadcast
        broadcast = None
        for msg in self.scheduled_messages:
            if msg['id'] == broadcast_id:
                broadcast = msg
                break
        
        if not broadcast:
            await query.edit_message_text("❌ Broadcast not found.")
            return
        
        # Show broadcast details and edit options
        status = "✅ Active" if broadcast.get('active', True) else "❌ Inactive"
        original_time = broadcast.get('original_time', f"UTC {broadcast['time']}")
        button_count = len(broadcast.get('buttons', []))
        
        edit_text = f"""
✏️ *Edit Broadcast #{broadcast['id']}*

🕰️ **Time:** {original_time}
📝 **Message:** {broadcast['message'][:100]}{'...' if len(broadcast['message']) > 100 else ''}
🔘 **Buttons:** {button_count}
📊 **Status:** {status}

**What would you like to edit?**
        """
        
        keyboard = [
            [InlineKeyboardButton("🕰️ Edit Time", callback_data=f"edit_time_{broadcast_id}"),
             InlineKeyboardButton("📝 Edit Message", callback_data=f"edit_message_{broadcast_id}")],
            [InlineKeyboardButton("🔘 Edit Buttons", callback_data=f"edit_buttons_{broadcast_id}"),
             InlineKeyboardButton("📊 Toggle Status", callback_data=f"toggle_status_{broadcast_id}")],
            [InlineKeyboardButton("🗑️ Delete Broadcast", callback_data=f"delete_broadcast_{broadcast_id}")],
            [InlineKeyboardButton("⬅️ Back to Edit List", callback_data="edit_broadcast")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                edit_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception:
            await query.message.reply_text(
                edit_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def show_daily_broadcast_management(self, query, user_id):
        """Show daily broadcast management options"""
        # Get all daily broadcasts
        daily_broadcasts = [msg for msg in self.scheduled_messages if msg.get('type') in ['daily', 'custom']]
        active_daily = [msg for msg in daily_broadcasts if msg.get('active', True)]
        inactive_daily = [msg for msg in daily_broadcasts if not msg.get('active', True)]
        
        broadcast_text = f"""
📅 *Daily Broadcast Management*

📊 **Overview:**
• Total Daily Broadcasts: {len(daily_broadcasts)}
• Active: {len(active_daily)}
• Inactive: {len(inactive_daily)}

🔁 **Active Daily Broadcasts:**
        """
        
        if not active_daily:
            broadcast_text += "❌ No active daily broadcasts\n\n"
        else:
            for i, msg in enumerate(active_daily, 1):
                original_time = msg.get('original_time', f"UTC {msg['time']}")
                broadcast_text += f"✅ **{i}.** {original_time}\n"
                broadcast_text += f"   📝 {msg['message'][:40]}{'...' if len(msg['message']) > 40 else ''}\n"
                if msg.get('buttons'):
                    broadcast_text += f"   🔘 {len(msg['buttons'])} button(s)\n"
                broadcast_text += "\n"
        
        if inactive_daily:
            broadcast_text += f"❌ **Inactive Daily Broadcasts ({len(inactive_daily)}):**\n"
            for i, msg in enumerate(inactive_daily, 1):
                original_time = msg.get('original_time', f"UTC {msg['time']}")
                broadcast_text += f"❌ **{i}.** {original_time}\n"
                broadcast_text += f"   📝 {msg['message'][:40]}{'...' if len(msg['message']) > 40 else ''}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ Create New Daily", callback_data="set_new_broadcast"),
             InlineKeyboardButton("👁️ View All", callback_data="view_broadcast")],
            [InlineKeyboardButton("✏️ Edit Daily", callback_data="edit_broadcast"),
             InlineKeyboardButton("📊 Manage Status", callback_data="manage_daily_status")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="daily_broadcast")],
            [InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                broadcast_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception:
            await query.message.reply_text(
                broadcast_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def show_daily_status_management(self, query, user_id):
        """Show status management for daily broadcasts"""
        daily_broadcasts = [msg for msg in self.scheduled_messages if msg.get('type') in ['daily', 'custom']]
        
        if not daily_broadcasts:
            status_text = "📊 *Daily Broadcast Status Management*\n\n"
            status_text += "❌ No daily broadcasts found."
            
            keyboard = [
                [InlineKeyboardButton("➕ Create New Daily", callback_data="set_new_broadcast")],
                [InlineKeyboardButton("⬅️ Back to Daily Management", callback_data="daily_broadcast")]
            ]
        else:
            status_text = "📊 *Daily Broadcast Status Management*\n\n"
            status_text += "Click to toggle status:\n\n"
            
            keyboard = []
            for msg in daily_broadcasts:
                status_icon = "✅" if msg.get('active', True) else "❌"
                original_time = msg.get('original_time', f"UTC {msg['time']}")
                button_text = f"{status_icon} {original_time}"
                
                if len(button_text) > 30:
                    button_text = button_text[:27] + "..."
                
                status_text += f"{status_icon} **{original_time}**\n"
                status_text += f"   📝 {msg['message'][:40]}{'...' if len(msg['message']) > 40 else ''}\n\n"
                
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"toggle_status_{msg['id']}")])
            
            keyboard.extend([
                [InlineKeyboardButton("🔄 Refresh", callback_data="manage_daily_status")],
                [InlineKeyboardButton("⬅️ Back to Daily Management", callback_data="daily_broadcast")]
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                status_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception:
            await query.message.reply_text(
                status_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def toggle_broadcast_status(self, query, user_id, broadcast_id):
        """Toggle the active status of a broadcast"""
        # Find the broadcast
        broadcast = None
        for msg in self.scheduled_messages:
            if msg['id'] == broadcast_id:
                broadcast = msg
                break
        
        if not broadcast:
            await query.edit_message_text("❌ Broadcast not found.")
            return
        
        # Toggle status
        old_status = broadcast.get('active', True)
        new_status = not old_status
        broadcast['active'] = new_status
        
        # Save changes
        self.save_scheduled_messages()
        
        # Show confirmation
        status_text = "✅ Active" if new_status else "❌ Inactive"
        original_time = broadcast.get('original_time', f"UTC {broadcast['time']}")
        
        result_text = f"""
✅ *Status Updated Successfully!*

🕰️ **Broadcast:** {original_time}
📊 **Status:** {status_text}

📝 The broadcast is now **{'active' if new_status else 'inactive'}**.
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 Manage Status", callback_data="manage_daily_status")],
            [InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                result_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception:
            await query.message.reply_text(
                result_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def confirm_delete_broadcast(self, query, user_id, broadcast_id):
        """Show confirmation dialog for deleting a broadcast"""
        # Find the broadcast
        broadcast = None
        for msg in self.scheduled_messages:
            if msg['id'] == broadcast_id:
                broadcast = msg
                break
        
        if not broadcast:
            await query.edit_message_text("❌ Broadcast not found.")
            return
        
        original_time = broadcast.get('original_time', f"UTC {broadcast['time']}")
        
        confirm_text = f"""
⚠️ *Delete Broadcast Confirmation*

🕰️ **Time:** {original_time}
📝 **Message:** {broadcast['message'][:60]}{'...' if len(broadcast['message']) > 60 else ''}

**Are you sure you want to delete this broadcast?**

⚠️ This action cannot be undone!
        """
        
        keyboard = [
            [InlineKeyboardButton("🗑️ Yes, Delete", callback_data=f"confirm_delete_{broadcast_id}"),
             InlineKeyboardButton("❌ Cancel", callback_data=f"edit_broadcast_{broadcast_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                confirm_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception:
            await query.message.reply_text(
                confirm_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def delete_broadcast(self, query, user_id, broadcast_id):
        """Delete a broadcast permanently"""
        # Find and remove the broadcast
        broadcast = None
        for i, msg in enumerate(self.scheduled_messages):
            if msg['id'] == broadcast_id:
                broadcast = self.scheduled_messages.pop(i)
                break
        
        if not broadcast:
            await query.edit_message_text("❌ Broadcast not found.")
            return
        
        # Save changes
        self.save_scheduled_messages()
        
        # Show confirmation
        original_time = broadcast.get('original_time', f"UTC {broadcast['time']}")
        
        result_text = f"""
✅ *Broadcast Deleted Successfully!*

🕰️ **Deleted:** {original_time}
📝 **Message:** {broadcast['message'][:60]}{'...' if len(broadcast['message']) > 60 else ''}

📋 The broadcast has been permanently removed from the schedule.
        """
        
        keyboard = [
            [InlineKeyboardButton("✏️ Edit More", callback_data="edit_broadcast")],
            [InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                result_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception:
            await query.message.reply_text(
                result_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def handle_broadcast_creation_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages during broadcast creation"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            return
        
        if user_id not in self.broadcast_states:
            return
        
        state = self.broadcast_states[user_id]
        message_text = update.message.text
        
        if state == 'waiting_for_text':
            # Store the text and ask for button count
            self.temp_broadcast_data[user_id]['text'] = message_text
            await self.ask_for_button_count(update.message, user_id)
            
        elif state.startswith('waiting_for_button_'):
            # Parse button text and action (URL or TEXT)
            if ' | ' in message_text:
                button_text, button_action = message_text.split(' | ', 1)
                button_num = int(state.split('_')[3])
                
                button_data = {'text': button_text.strip()}
                
                if button_action.strip().upper() == 'TEXT':
                    # Text response button
                    button_data['callback_data'] = f"text_response_{button_num}"
                else:
                    # URL button
                    button_data['url'] = button_action.strip()
                
                self.temp_broadcast_data[user_id]['buttons'].append(button_data)
                
                button_count = self.temp_broadcast_data[user_id]['button_count']
                
                if button_num < button_count:
                    # Ask for next button
                    await self.ask_for_next_button(update.message, user_id, button_num + 1)
                else:
                    # All buttons collected, show preview
                    await self.show_broadcast_preview(update.message, user_id)
            else:
                await update.message.reply_text(
                    "❌ Invalid format! Please use: ButtonText | URL or ButtonText | TEXT"
                )
        
        elif state == 'waiting_for_schedule_time':
            # Parse timezone format: UTC+5:30 19:48 or UTC-5 14:30
            try:
                # Parse input like "UTC+5:30 19:48" or "UTC+6 19:48"
                if message_text.upper().startswith('UTC') and ' ' in message_text:
                    timezone_part, time_part = message_text.split(' ', 1)
                    
                    # Parse timezone offset
                    if '+' in timezone_part:
                        offset_str = timezone_part.split('+')[1]
                        offset_sign = 1
                    elif '-' in timezone_part:
                        offset_str = timezone_part.split('-')[1]
                        offset_sign = -1
                    else:
                        offset_str = '0'
                        offset_sign = 1
                    
                    # Parse offset hours and minutes
                    if ':' in offset_str:
                        offset_hours, offset_minutes = map(int, offset_str.split(':'))
                    else:
                        offset_hours = int(offset_str)
                        offset_minutes = 0
                    
                    # Parse time
                    if ':' in time_part:
                        hour, minute = map(int, time_part.split(':'))
                        
                        if 0 <= hour <= 23 and 0 <= minute <= 59:
                            # Convert user timezone to UTC
                            # For UTC+5:30 19:27 -> UTC time = 19:27 - 5:30 = 13:57
                            # For UTC-5 14:30 -> UTC time = 14:30 + 5 = 19:30
                            
                            total_offset_minutes = offset_sign * (offset_hours * 60 + offset_minutes)
                            
                            # Create datetime object for today at the specified time
                            user_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                            
                            # Convert to UTC by subtracting the timezone offset
                            utc_time = user_time - timedelta(minutes=total_offset_minutes)
                            
                            utc_time_str = utc_time.strftime('%H:%M')
                            
                            # Verification message for debugging
                            print(f"DEBUG: {timezone_part} {time_part} -> UTC {utc_time_str}")
                            print(f"DEBUG: Offset: {offset_sign} * ({offset_hours}h + {offset_minutes}m) = {total_offset_minutes} minutes")
                            
                            # Store both original and UTC times
                            self.temp_broadcast_data[user_id]['schedule_time'] = utc_time_str
                            self.temp_broadcast_data[user_id]['original_time'] = f"{timezone_part} {time_part}"
                            
                            # Ask for frequency (today only or daily)
                            await self.ask_broadcast_frequency(update.message, user_id)
                        else:
                            await update.message.reply_text(
                                "❌ Invalid time! Hour must be 0-23, minute must be 0-59."
                            )
                    else:
                        await update.message.reply_text(
                            "❌ Invalid time format in time part! Use HH:MM format."
                        )
                else:
                    await update.message.reply_text(
                        "❌ Invalid format! Please use: UTC[+/-offset] HH:MM\n\nExamples:\n• UTC+5:30 19:48\n• UTC+6 14:30\n• UTC-5 09:15"
                    )
            except (ValueError, IndexError) as e:
                await update.message.reply_text(
                    "❌ Invalid format! Please use: UTC[+/-offset] HH:MM\n\nExamples:\n• UTC+5:30 19:48\n• UTC+6 14:30\n• UTC-5 09:15"
                )
        
        elif state.startswith('editing_time_'):
            # Handle editing broadcast time
            broadcast_id = int(state.split('_')[2])
            await self.handle_edit_time(update.message, user_id, broadcast_id, message_text)
            
        elif state.startswith('editing_message_'):
            # Handle editing broadcast message
            broadcast_id = int(state.split('_')[2])
            await self.handle_edit_message(update.message, user_id, broadcast_id, message_text)
        
        elif state.startswith('recreating_button_'):
            # Handle button recreation: recreating_button_X_broadcastid
            parts = state.split('_')
            button_num = int(parts[2])
            broadcast_id = int(parts[3])
            
            # Parse button text and action (URL or TEXT)
            if ' | ' in message_text:
                button_text, button_action = message_text.split(' | ', 1)
                
                button_data = {'text': button_text.strip()}
                
                if button_action.strip().upper() == 'TEXT':
                    # Text response button
                    button_data['callback_data'] = f"text_response_{button_num}"
                else:
                    # URL button
                    button_data['url'] = button_action.strip()
                
                self.temp_broadcast_data[user_id]['buttons'].append(button_data)
                
                button_count = self.temp_broadcast_data[user_id]['button_count']
                
                if button_num < button_count:
                    # Ask for next button
                    self.broadcast_states[user_id] = f'recreating_button_{button_num + 1}_{broadcast_id}'
                    await self.ask_for_recreate_button_details(update.message, user_id, button_num + 1, button_count, broadcast_id)
                else:
                    # All buttons collected, apply them
                    buttons = self.temp_broadcast_data[user_id]['buttons']
                    await self.apply_recreated_buttons_from_message(update.message, user_id, broadcast_id, buttons)
            else:
                await update.message.reply_text(
                    "❌ Invalid format! Please use: ButtonText | URL or ButtonText | TEXT"
                )
        
        elif state.startswith('adding_button_'):
            # Handle adding a single button: adding_button_broadcastid
            broadcast_id = int(state.split('_')[2])
            
            # Parse button text and action (URL or TEXT)
            if ' | ' in message_text:
                button_text, button_action = message_text.split(' | ', 1)
                
                button_data = {'text': button_text.strip()}
                
                if button_action.strip().upper() == 'TEXT':
                    # Text response button
                    button_data['callback_data'] = f"text_response_add"
                else:
                    # URL button
                    button_data['url'] = button_action.strip()
                
                # Add this button to existing broadcast
                await self.add_single_button_to_broadcast(update.message, user_id, broadcast_id, button_data)
            else:
                await update.message.reply_text(
                    "❌ Invalid format! Please use: ButtonText | URL or ButtonText | TEXT"
                )
    
    async def show_broadcast_preview(self, update, user_id):
        """Show preview of the broadcast before sending"""
        data = self.temp_broadcast_data[user_id]
        
        preview_text = f"""
🔍 *Broadcast Preview*

{data['text']}

📊 *Statistics:*
• Will be sent to: {len(self.subscribers)} subscribers
• Buttons: {len(data['buttons'])}
        """
        
        # Create preview buttons
        keyboard = []
        for button in data['buttons']:
            if 'url' in button:
                keyboard.append([InlineKeyboardButton(button['text'], url=button['url'])])
            else:
                keyboard.append([InlineKeyboardButton(button['text'], callback_data=button['callback_data'])])
        
        # Add control buttons
        keyboard.extend([
            [InlineKeyboardButton("🚀 Send Now", callback_data="send_now_broadcast"),
             InlineKeyboardButton("🕰️ Schedule", callback_data="schedule_broadcast")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_broadcast")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send preview with image if available
        try:
            if data['image'] and os.path.exists(data['image']):
                with open(data['image'], 'rb') as photo:
                    await update.reply_photo(
                        photo=photo,
                        caption=preview_text,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=reply_markup
                    )
            else:
                await update.reply_text(
                    preview_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
        except Exception as e:
            logger.warning(f"Failed to send preview: {e}")
            await update.reply_text(
                preview_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def send_broadcast_now(self, query, user_id):
        """Send broadcast immediately"""
        data = self.temp_broadcast_data[user_id]
        
        # Create keyboard for broadcast
        keyboard = []
        for button in data['buttons']:
            if 'url' in button:
                keyboard.append([InlineKeyboardButton(button['text'], url=button['url'])])
            else:
                keyboard.append([InlineKeyboardButton(button['text'], callback_data=button['callback_data'])])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send broadcast to all subscribers
        success_count = 0
        failed_count = 0
        
        for chat_id in self.subscribers.copy():
            try:
                if data['image'] and os.path.exists(data['image']):
                    with open(data['image'], 'rb') as photo:
                        await self.application.bot.send_photo(
                            chat_id=chat_id,
                            photo=photo,
                            caption=data['text'],
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=reply_markup
                        )
                else:
                    await self.application.bot.send_message(
                        chat_id=chat_id,
                        text=data['text'],
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=reply_markup
                    )
                success_count += 1
                await asyncio.sleep(0.05)  # Rate limiting
                
            except Exception as e:
                failed_count += 1
                if "blocked" in str(e).lower() or "not found" in str(e).lower():
                    self.remove_subscriber(chat_id)
                logger.warning(f"Failed to send broadcast to {chat_id}: {e}")
        
        # Clear broadcast state
        if user_id in self.broadcast_states:
            del self.broadcast_states[user_id]
        if user_id in self.temp_broadcast_data:
            del self.temp_broadcast_data[user_id]
        
        # Show results
        result_text = f"""
✅ *Broadcast Sent Successfully!*

📊 *Results:*
• Successfully sent: {success_count}
• Failed: {failed_count}
• Total subscribers: {len(self.subscribers)}
        """
        
        keyboard = [
            [InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                result_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception as e:
            # If editing fails (likely because it's an image message), send a new message
            await query.message.reply_text(
                result_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def schedule_broadcast(self, update, user_id):
        """Schedule broadcast for specific time"""
        data = self.temp_broadcast_data[user_id]
        schedule_time = data['schedule_time']
        
        # Add to scheduled messages
        new_scheduled_msg = {
            "id": len(self.scheduled_messages) + 1,
            "time": schedule_time,
            "message": data['text'],
            "active": True,
            "type": "custom",
            "image": data['image'],
            "buttons": data['buttons']
        }
        
        self.scheduled_messages.append(new_scheduled_msg)
        self.save_scheduled_messages()
        
        # Add to scheduler
        schedule.every().day.at(schedule_time).do(
            self.run_custom_scheduled_broadcast,
            new_scheduled_msg
        )
        
        # Clear broadcast state
        if user_id in self.broadcast_states:
            del self.broadcast_states[user_id]
        if user_id in self.temp_broadcast_data:
            del self.temp_broadcast_data[user_id]
        
        # Calculate IST equivalent
        utc_hour, utc_minute = map(int, schedule_time.split(':'))
        utc_dt = datetime.now().replace(hour=utc_hour, minute=utc_minute, second=0, microsecond=0)
        ist_dt = utc_dt + timedelta(hours=5, minutes=30)
        ist_time = ist_dt.strftime('%H:%M')
        
        # Show confirmation
        result_text = f"""
✅ *Broadcast Scheduled Successfully!*

🕰️ *Schedule Details:*
• UTC Time: {schedule_time} (Daily)
• IST Time: {ist_time} (+5:30)
• Recipients: {len(self.subscribers)} subscribers
• Status: Active

📝 The broadcast will be sent automatically at the scheduled time every day.
        """
        
        keyboard = [
            [InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.reply_text(
            result_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    def run_custom_scheduled_broadcast(self, scheduled_msg):
        """Run custom scheduled broadcast"""
        if self.application:
            asyncio.create_task(self.send_custom_broadcast(scheduled_msg))
    
    async def send_custom_broadcast(self, scheduled_msg):
        """Send custom scheduled broadcast"""
        # Create keyboard
        keyboard = []
        for button in scheduled_msg.get('buttons', []):
            if 'url' in button:
                keyboard.append([InlineKeyboardButton(button['text'], url=button['url'])])
            else:
                keyboard.append([InlineKeyboardButton(button['text'], callback_data=button['callback_data'])])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        success_count = 0
        failed_count = 0
        
        for chat_id in self.subscribers.copy():
            try:
                if scheduled_msg.get('image') and os.path.exists(scheduled_msg['image']):
                    with open(scheduled_msg['image'], 'rb') as photo:
                        await self.application.bot.send_photo(
                            chat_id=chat_id,
                            photo=photo,
                            caption=scheduled_msg['message'],
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=reply_markup
                        )
                else:
                    await self.application.bot.send_message(
                        chat_id=chat_id,
                        text=scheduled_msg['message'],
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=reply_markup
                    )
                success_count += 1
                await asyncio.sleep(0.05)
                
            except Exception as e:
                failed_count += 1
                if "blocked" in str(e).lower() or "not found" in str(e).lower():
                    self.remove_subscriber(chat_id)
                logger.warning(f"Failed to send scheduled broadcast to {chat_id}: {e}")
        
        logger.info(f"Custom scheduled broadcast sent: {success_count} success, {failed_count} failed")
    
    async def schedule_broadcast_once(self, query, user_id):
        """Schedule broadcast for today only"""
        data = self.temp_broadcast_data[user_id]
        schedule_time = data['schedule_time']
        original_time = data['original_time']
        
        # Create a one-time job using UTC time
        utc_hour = int(schedule_time.split(':')[0])
        utc_minute = int(schedule_time.split(':')[1])
        
        # Get current UTC time
        utc_now = datetime.utcnow()
        target_datetime = utc_now.replace(
            hour=utc_hour,
            minute=utc_minute,
            second=0,
            microsecond=0
        )
        
        # If the UTC time has already passed today, schedule for tomorrow
        if target_datetime <= utc_now:
            target_datetime += timedelta(days=1)
            schedule_date = "Tomorrow"
        else:
            schedule_date = "Today"
        
        print(f"DEBUG: Current UTC: {utc_now.strftime('%H:%M:%S')}")
        print(f"DEBUG: Target UTC: {target_datetime.strftime('%H:%M:%S')} ({schedule_date})")
        
        # Store one-time broadcast data
        one_time_broadcast = {
            "datetime": target_datetime,
            "message": data['text'],
            "image": data['image'],
            "buttons": data['buttons'],
            "original_time": original_time
        }
        
        # Add to one-time broadcasts list
        self.one_time_broadcasts.append(one_time_broadcast)
        print(f"DEBUG: Added one-time broadcast for {target_datetime} UTC")
        print(f"DEBUG: Total one-time broadcasts: {len(self.one_time_broadcasts)}")
        
        # Clear broadcast state
        if user_id in self.broadcast_states:
            del self.broadcast_states[user_id]
        if user_id in self.temp_broadcast_data:
            del self.temp_broadcast_data[user_id]
        
        # Show confirmation
        result_text = f"""
✅ *Broadcast Scheduled Successfully!*

🕰️ *Schedule Details:*
• Original Time: {original_time}
• UTC Time: {schedule_time}
• Date: {schedule_date} {target_datetime.strftime('%Y-%m-%d')}
• Recipients: {len(self.subscribers)} subscribers
• Frequency: **Today Only**

📝 The broadcast will be sent once at the scheduled time.
        """
        
        keyboard = [
            [InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                result_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception:
            await query.message.reply_text(
                result_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def schedule_broadcast_daily(self, query, user_id):
        """Schedule broadcast for daily"""
        data = self.temp_broadcast_data[user_id]
        schedule_time = data['schedule_time']
        original_time = data['original_time']
        
        # Add to scheduled messages
        new_scheduled_msg = {
            "id": len(self.scheduled_messages) + 1,
            "time": schedule_time,
            "message": data['text'],
            "active": True,
            "type": "custom",
            "image": data['image'],
            "buttons": data['buttons'],
            "original_time": original_time
        }
        
        self.scheduled_messages.append(new_scheduled_msg)
        self.save_scheduled_messages()
        
        # Add to scheduler
        schedule.every().day.at(schedule_time).do(
            self.run_custom_scheduled_broadcast,
            new_scheduled_msg
        )
        
        # Clear broadcast state
        if user_id in self.broadcast_states:
            del self.broadcast_states[user_id]
        if user_id in self.temp_broadcast_data:
            del self.temp_broadcast_data[user_id]
        
        # Show confirmation
        result_text = f"""
✅ *Broadcast Scheduled Successfully!*

🕰️ *Schedule Details:*
• Original Time: {original_time}
• UTC Time: {schedule_time}
• Recipients: {len(self.subscribers)} subscribers
• Frequency: **Daily**

📝 The broadcast will be sent automatically every day at the scheduled time.
        """
        
        keyboard = [
            [InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                result_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception:
            await query.message.reply_text(
                result_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def handle_edit_time(self, message, user_id, broadcast_id, new_time_text):
        """Handle editing broadcast time"""
        try:
            # Parse the new time using the same logic as scheduling
            if new_time_text.upper().startswith('UTC') and ' ' in new_time_text:
                timezone_part, time_part = new_time_text.split(' ', 1)
                
                # Parse timezone offset
                if '+' in timezone_part:
                    offset_str = timezone_part.split('+')[1]
                    offset_sign = 1
                elif '-' in timezone_part:
                    offset_str = timezone_part.split('-')[1]
                    offset_sign = -1
                else:
                    offset_str = '0'
                    offset_sign = 1
                
                # Parse offset hours and minutes
                if ':' in offset_str:
                    offset_hours, offset_minutes = map(int, offset_str.split(':'))
                else:
                    offset_hours = int(offset_str)
                    offset_minutes = 0
                
                # Parse time
                if ':' in time_part:
                    hour, minute = map(int, time_part.split(':'))
                    
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        # Convert to UTC
                        total_offset_minutes = offset_sign * (offset_hours * 60 + offset_minutes)
                        user_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                        utc_time = user_time - timedelta(minutes=total_offset_minutes)
                        utc_time_str = utc_time.strftime('%H:%M')
                        
                        # Find and update the broadcast
                        for msg in self.scheduled_messages:
                            if msg['id'] == broadcast_id:
                                old_time = msg.get('original_time', f"UTC {msg['time']}")
                                msg['time'] = utc_time_str
                                msg['original_time'] = f"{timezone_part} {time_part}"
                                break
                        
                        # Save changes
                        self.save_scheduled_messages()
                        
                        # Clear edit state
                        if user_id in self.broadcast_states:
                            del self.broadcast_states[user_id]
                        
                        # Show confirmation
                        result_text = f"""
✅ *Time Updated Successfully!*

🕰️ **Old Time:** {old_time}
🕰️ **New Time:** {timezone_part} {time_part}
🌍 **UTC Time:** {utc_time_str}

📝 The broadcast time has been updated.
                        """
                        
                        keyboard = [
                            [InlineKeyboardButton("✏️ Edit More", callback_data=f"edit_broadcast_{broadcast_id}")],
                            [InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        await message.reply_text(
                            result_text,
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=reply_markup
                        )
                        return
            
            # Invalid format
            await message.reply_text(
                "❌ Invalid format! Please use: UTC[+/-offset] HH:MM\n\nExamples:\n• UTC+5:30 19:48\n• UTC+6 14:30\n• UTC-5 09:15"
            )
            
        except Exception as e:
            await message.reply_text(
                "❌ Invalid time format! Please use: UTC[+/-offset] HH:MM\n\nExamples:\n• UTC+5:30 19:48\n• UTC+6 14:30\n• UTC-5 09:15"
            )
    
    async def handle_edit_message(self, message, user_id, broadcast_id, new_message):
        """Handle editing broadcast message"""
        # Find and update the broadcast
        broadcast_found = False
        old_message = ""
        
        for msg in self.scheduled_messages:
            if msg['id'] == broadcast_id:
                old_message = msg['message']
                msg['message'] = new_message
                broadcast_found = True
                break
        
        if not broadcast_found:
            await message.reply_text("❌ Broadcast not found.")
            return
        
        # Save changes
        self.save_scheduled_messages()
        
        # Clear edit state
        if user_id in self.broadcast_states:
            del self.broadcast_states[user_id]
        
        # Show confirmation
        result_text = f"""
✅ *Message Updated Successfully!*

📋 **Old Message:**
{old_message[:100]}{'...' if len(old_message) > 100 else ''}

✨ **New Message:**
{new_message[:100]}{'...' if len(new_message) > 100 else ''}

📝 The broadcast message has been updated.
        """
        
        keyboard = [
            [InlineKeyboardButton("✏️ Edit More", callback_data=f"edit_broadcast_{broadcast_id}")],
            [InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            result_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_edit_buttons_options(self, query, user_id, broadcast_id):
        """Show button editing options"""
        # Find the broadcast
        broadcast = None
        for msg in self.scheduled_messages:
            if msg['id'] == broadcast_id:
                broadcast = msg
                break
        
        if not broadcast:
            await query.edit_message_text("❌ Broadcast not found.")
            return
        
        current_buttons = broadcast.get('buttons', [])
        button_count = len(current_buttons)
        
        edit_text = f"""
🔘 *Edit Buttons for Broadcast*

📋 **Current Buttons:** {button_count}
        """
        
        if current_buttons:
            for i, button in enumerate(current_buttons, 1):
                button_type = "URL" if 'url' in button else "Text"
                edit_text += f"\n**{i}.** {button['text']} ({button_type})"
        else:
            edit_text += "\n❌ No buttons currently set"
        
        edit_text += "\n\n**What would you like to do?**"
        
        keyboard = [
            [InlineKeyboardButton("➕ Add New Button", callback_data=f"add_button_{broadcast_id}")],
            [InlineKeyboardButton("🗿 Clear All Buttons", callback_data=f"clear_buttons_{broadcast_id}")],
            [InlineKeyboardButton("✏️ Recreate All", callback_data=f"recreate_buttons_{broadcast_id}")],
            [InlineKeyboardButton("⬅️ Back to Edit", callback_data=f"edit_broadcast_{broadcast_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                edit_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception:
            await query.message.reply_text(
                edit_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def clear_broadcast_buttons(self, query, user_id, broadcast_id):
        """Clear all buttons from a broadcast"""
        # Find and update the broadcast
        broadcast = None
        for msg in self.scheduled_messages:
            if msg['id'] == broadcast_id:
                broadcast = msg
                break
        
        if not broadcast:
            await query.edit_message_text("❌ Broadcast not found.")
            return
        
        # Clear buttons
        old_button_count = len(broadcast.get('buttons', []))
        broadcast['buttons'] = []
        
        # Save changes
        self.save_scheduled_messages()
        
        result_text = f"""
✅ *Buttons Cleared Successfully!*

🗿 **Removed:** {old_button_count} button(s)
🔘 **Current:** 0 buttons

📝 The broadcast now has no buttons.
        """
        
        keyboard = [
            [InlineKeyboardButton("➕ Add Buttons", callback_data=f"recreate_buttons_{broadcast_id}")],
            [InlineKeyboardButton("✏️ Edit More", callback_data=f"edit_broadcast_{broadcast_id}")],
            [InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                result_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception:
            await query.message.reply_text(
                result_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def start_recreate_buttons(self, query, user_id, broadcast_id):
        """Start the process of recreating buttons"""
        # Store editing state
        self.broadcast_states[user_id] = f'recreating_buttons_{broadcast_id}'
        self.temp_broadcast_data[user_id] = {
            'editing_broadcast_id': broadcast_id,
            'buttons': []
        }
        
        # Ask for button count
        button_text = f"""
🔘 *Recreate Buttons*

🔢 *Step: Choose Button Count*
How many buttons do you want for this broadcast?

Select 0-3 buttons:
        """
        
        keyboard = [
            [InlineKeyboardButton("❌ No Button", callback_data=f"recreate_count_0_{broadcast_id}")],
            [InlineKeyboardButton("1️⃣ One Button", callback_data=f"recreate_count_1_{broadcast_id}")],
            [InlineKeyboardButton("2️⃣ Two Buttons", callback_data=f"recreate_count_2_{broadcast_id}")],
            [InlineKeyboardButton("3️⃣ Three Buttons", callback_data=f"recreate_count_3_{broadcast_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"edit_buttons_{broadcast_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                button_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception:
            await query.message.reply_text(
                button_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def ask_for_recreate_button_details(self, query, user_id, button_num, total_buttons, broadcast_id):
        """Ask for button text and link during recreation"""
        button_text = f"""
🔘 *Recreate Button {button_num}/{total_buttons}*

Please provide button text and action for Button {button_num}:

🔗 *For URL Button:*
Format: ButtonText | https://your-link.com
Example: Start Earning | https://t.me/Letssgrowbot/Earn

💬 *For Text Response Button:*
Format: ButtonText | TEXT
Example: Get Help | TEXT

Type your response and send it.
        """
        
        keyboard = [
            [InlineKeyboardButton("❌ Cancel", callback_data=f"edit_buttons_{broadcast_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                button_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception:
            await query.message.reply_text(
                button_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def apply_recreated_buttons(self, query, user_id, broadcast_id, buttons):
        """Apply the recreated buttons to the broadcast"""
        # Find and update the broadcast
        broadcast = None
        for msg in self.scheduled_messages:
            if msg['id'] == broadcast_id:
                broadcast = msg
                break
        
        if not broadcast:
            await query.edit_message_text("❌ Broadcast not found.")
            return
        
        # Update buttons
        old_button_count = len(broadcast.get('buttons', []))
        broadcast['buttons'] = buttons
        
        # Save changes
        self.save_scheduled_messages()
        
        # Clear editing state
        if user_id in self.broadcast_states:
            del self.broadcast_states[user_id]
        if user_id in self.temp_broadcast_data:
            del self.temp_broadcast_data[user_id]
        
        result_text = f"""
✅ *Buttons Updated Successfully!*

🔘 **Old Buttons:** {old_button_count}
🔘 **New Buttons:** {len(buttons)}

📝 The broadcast buttons have been updated.
        """
        
        if buttons:
            result_text += "\n\n**New Buttons:**\n"
            for i, button in enumerate(buttons, 1):
                button_type = "URL" if 'url' in button else "Text"
                result_text += f"**{i}.** {button['text']} ({button_type})\n"
        
        keyboard = [
            [InlineKeyboardButton("🔘 Edit Buttons", callback_data=f"edit_buttons_{broadcast_id}")],
            [InlineKeyboardButton("✏️ Edit More", callback_data=f"edit_broadcast_{broadcast_id}")],
            [InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                result_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception:
            await query.message.reply_text(
                result_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def start_add_single_button(self, query, user_id, broadcast_id):
        """Start adding a single button to existing broadcast"""
        # Find the broadcast to check current button count
        broadcast = None
        for msg in self.scheduled_messages:
            if msg['id'] == broadcast_id:
                broadcast = msg
                break
        
        if not broadcast:
            await query.edit_message_text("❌ Broadcast not found.")
            return
        
        current_buttons = broadcast.get('buttons', [])
        
        if len(current_buttons) >= 3:
            # Maximum buttons reached
            await query.edit_message_text(
                "❌ **Maximum Buttons Reached**\n\nYou can have maximum 3 buttons per broadcast.\n\nPlease clear some buttons first or recreate all buttons.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Store editing state
        self.broadcast_states[user_id] = f'adding_button_{broadcast_id}'
        
        button_text = f"""
➕ *Add New Button*

📊 **Current Buttons:** {len(current_buttons)}/3

Please provide button text and action:

🔗 *For URL Button:*
Format: ButtonText | https://your-link.com
Example: Start Earning | https://t.me/Letssgrowbot/Earn

💬 *For Text Response Button:*
Format: ButtonText | TEXT
Example: Get Help | TEXT

Type your response and send it.
        """
        
        keyboard = [
            [InlineKeyboardButton("❌ Cancel", callback_data=f"edit_buttons_{broadcast_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                button_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception:
            await query.message.reply_text(
                button_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def apply_recreated_buttons_from_message(self, message, user_id, broadcast_id, buttons):
        """Apply recreated buttons from text message response"""
        # Find and update the broadcast
        broadcast = None
        for msg in self.scheduled_messages:
            if msg['id'] == broadcast_id:
                broadcast = msg
                break
        
        if not broadcast:
            await message.reply_text("❌ Broadcast not found.")
            return
        
        # Update buttons
        old_button_count = len(broadcast.get('buttons', []))
        broadcast['buttons'] = buttons
        
        # Save changes
        self.save_scheduled_messages()
        
        # Clear editing state
        if user_id in self.broadcast_states:
            del self.broadcast_states[user_id]
        if user_id in self.temp_broadcast_data:
            del self.temp_broadcast_data[user_id]
        
        result_text = f"""
✅ *Buttons Updated Successfully!*

🔘 **Old Buttons:** {old_button_count}
🔘 **New Buttons:** {len(buttons)}

📝 The broadcast buttons have been updated.
        """
        
        if buttons:
            result_text += "\n\n**New Buttons:**\n"
            for i, button in enumerate(buttons, 1):
                button_type = "URL" if 'url' in button else "Text"
                result_text += f"**{i}.** {button['text']} ({button_type})\n"
        
        keyboard = [
            [InlineKeyboardButton("🔘 Edit Buttons", callback_data=f"edit_buttons_{broadcast_id}")],
            [InlineKeyboardButton("✏️ Edit More", callback_data=f"edit_broadcast_{broadcast_id}")],
            [InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            result_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def add_single_button_to_broadcast(self, message, user_id, broadcast_id, button_data):
        """Add a single button to an existing broadcast"""
        # Find the broadcast
        broadcast = None
        for msg in self.scheduled_messages:
            if msg['id'] == broadcast_id:
                broadcast = msg
                break
        
        if not broadcast:
            await message.reply_text("❌ Broadcast not found.")
            return
        
        # Make sure buttons list exists
        if 'buttons' not in broadcast:
            broadcast['buttons'] = []
        
        # Add the button
        broadcast['buttons'].append(button_data)
        
        # Save changes
        self.save_scheduled_messages()
        
        # Clear editing state
        if user_id in self.broadcast_states:
            del self.broadcast_states[user_id]
        
        button_type = "URL" if 'url' in button_data else "Text"
        button_action = button_data.get('url', "Text Response")
        
        result_text = f"""
✅ *Button Added Successfully!*

📊 **Button Details:**
• Text: {button_data['text']}
• Type: {button_type}
• {'URL' if 'url' in button_data else 'Action'}: {button_action}

🔘 **Total Buttons:** {len(broadcast['buttons'])}/3
        """
        
        keyboard = [
            [InlineKeyboardButton("➕ Add Another", callback_data=f"add_button_{broadcast_id}")],
            [InlineKeyboardButton("🔘 Manage Buttons", callback_data=f"edit_buttons_{broadcast_id}")],
            [InlineKeyboardButton("⬅️ Back to Edit", callback_data=f"edit_broadcast_{broadcast_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            result_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def ask_for_recreate_button_details(self, message, user_id, button_num, total_buttons, broadcast_id):
        """Ask for button details from message handler (not callback)"""
        button_text = f"""
🔘 *Recreate Button {button_num}/{total_buttons}*

Please provide button text and action for Button {button_num}:

🔗 *For URL Button:*
Format: ButtonText | https://your-link.com
Example: Start Earning | https://t.me/Letssgrowbot/Earn

💬 *For Text Response Button:*
Format: ButtonText | TEXT
Example: Get Help | TEXT

Type your response and send it.
        """
        
        keyboard = [
            [InlineKeyboardButton("❌ Cancel", callback_data=f"edit_buttons_{broadcast_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            button_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command"""
        chat_id = update.effective_chat.id
        removed = self.remove_subscriber(chat_id)
        
        if removed:
            message = "😢 You've been unsubscribed from broadcasts.\n\nSend /start anytime to subscribe again!"
        else:
            message = "You weren't subscribed to broadcasts.\n\nSend /start to subscribe!"
        
        await update.message.reply_text(message)
    
    def run(self):
        """Run the bot with scheduler"""
        self.application = Application.builder().token(self.bot_token).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("stop", self.stop_command))
        self.application.add_handler(CommandHandler("schedule", self.schedule_command))
        self.application.add_handler(CommandHandler("broadcast", self.broadcast_command))
        self.application.add_handler(CommandHandler("addschedule", self.add_schedule_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Add callback query handler for buttons
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Add message handler for broadcast creation
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_broadcast_creation_message))
        
        # Setup scheduler
        self.setup_scheduler()
        
        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info("Scheduled Broadcast Bot started successfully!")
        print("🤖 Scheduled Telegram Broadcast Bot is running...")
        print(f"👥 Current subscribers: {len(self.subscribers)}")
        print(f"⏰ Active schedules: {len([m for m in self.scheduled_messages if m['active']])}")
        print("📅 Scheduled broadcasts will run automatically!")
        print("Press Ctrl+C to stop")
        
        # Run the bot
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    # Install schedule if not available
    try:
        import schedule
    except ImportError:
        print("Installing schedule package...")
        os.system('pip install schedule')
        import schedule
    
    bot = ScheduledTelegramBot()
    bot.run()