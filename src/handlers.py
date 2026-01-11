from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from datetime import datetime
import re

from src.database import db
from src.utils import is_admin, format_targets_message

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued in a group."""
    if not update.message:
        return
    
    chat_id = update.message.chat.id
    chat_type = update.message.chat.type
    
    # Only respond in groups/supergroups
    if chat_type not in ["group", "supergroup"]:
        return  # Private chat handled by registration module
    
    # Check if group is allowed
    if not db.is_group_allowed(chat_id):
        # Set this group as allowed (first group that uses /start)
        group_name = update.message.chat.title or f"Group_{chat_id}"
        db.set_allowed_group(chat_id, group_name)
        await update.message.reply_text(
            f"✅ *Group Authorized!*\n\n"
            f"This group ({group_name}) has been registered as the authorized group.\n"
            f"Bot is now active here!\n\n"
            f"🔐 *Registration System Enabled:*\n"
            f"New members will be muted until they register via DM with the bot.",
            parse_mode="Markdown"
        )
    
    welcome_message = (
        "🎯 *Target Tracker Bot*\n\n"
        "I help track daily targets for group members!\n\n"
        "*Available Commands:*\n"
        "📌 /addtarget <target> - Add your target for today\n"
        "📌 /mytarget - Check your today's target\n"
        "📌 /today - See all targets for today\n"
        "📌 /mytargets - See your recent targets (last 7 days)\n"
        "📌 /done - Mark today's target as completed\n\n"
        "*Admin Commands:*\n"
        "🛠 /reset - Clear all bot data (testing only)\n"
        "🛠 /addtargetfor @username <target> - Add target for a user\n"
        "🛠 /status - Check bot status\n"
        "🛠 /help - Show this help message\n\n"
        "🔐 *New Members:*\n"
        "New members will be muted and need to register via DM"
    )
    
    await update.message.reply_text(welcome_message, parse_mode="Markdown")

# ... (rest of the handlers remain the same as before, just add this at the end)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages in groups."""
    if not update.message:
        return
    
    # Check if message is in a group
    if update.message.chat.type in ["group", "supergroup"]:
        group_id = update.message.chat.id
        
        # Check if group is allowed
        if not db.is_group_allowed(group_id):
            # Silently ignore messages from unauthorized groups
            return
        
        # Check if user is verified (for new members)
        user_id = update.message.from_user.id
        if not db.is_user_verified(user_id, group_id):
            # User is not verified, check if they're muted
            if db.is_user_muted(user_id, group_id):
                # User is still muted, delete their message
                try:
                    await update.message.delete()
                    
                    # Send reminder
                    registration = db.get_registration(user_id, group_id)
                    if registration and registration.get('verification_code'):
                        await update.message.reply_text(
                            f"⚠️ @{update.message.from_user.username or update.message.from_user.first_name}, "
                            f"you need to register first!\n"
                            f"Check your DM for verification code.",
                            reply_to_message_id=update.message.message_id
                        )
                except:
                    pass  # Couldn't delete message
            return
        
        # You can add additional message handling here
        # For example, reacting to certain keywords
        text = update.message.text.lower()
        
        if any(word in text for word in ["target", "goal", "task", "todo"]):
            await update.message.reply_text(
                "🎯 Don't forget to set your daily target with /addtarget !"
            )
