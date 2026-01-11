from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from datetime import datetime
import re

from src.database import db
from src.utils import is_admin, format_targets_message

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    if not update.message:
        return
    
    group_id = update.message.chat.id
    chat_type = update.message.chat.type
    
    if chat_type != "group" and chat_type != "supergroup":
        await update.message.reply_text("⚠️ This bot only works in groups!")
        return
    
    # Check if group is allowed
    if not db.is_group_allowed(group_id):
        await update.message.reply_text("🚫 This bot is not authorized to work in this group!")
        return
    
    group_name = update.message.chat.title or "Unknown Group"
    db.set_allowed_group(group_id, group_name)
    
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
        "🛠 /help - Show this help message"
    )
    
    await update.message.reply_text(welcome_message, parse_mode="Markdown")

async def add_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a target for today."""
    if not update.message:
        return
    
    group_id = update.message.chat.id
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    
    # Check if group is allowed
    if not db.is_allowed_group(group_id):
        await update.message.reply_text("🚫 This bot is not authorized to work in this group!")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Please provide your target!\nUsage: /addtarget <your target>")
        return
    
    target = " ".join(context.args)
    
    if db.add_target(group_id, user_id, username, target):
        await update.message.reply_text(f"✅ Target added!\n📝 *Your Target:* {target}", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Failed to add target. Please try again.")

async def add_target_for_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to add target for a specific user."""
    if not update.message:
        return
    
    group_id = update.message.chat.id
    admin_id = update.message.from_user.id
    
    # Check if user is admin
    if not await is_admin(update, context):
        await update.message.reply_text("🚫 This command is for admins only!")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /addtargetfor @username <target>")
        return
    
    # Extract username (remove @ if present)
    username = context.args[0].lstrip('@')
    target = " ".join(context.args[1:])
    
    # In a real implementation, you'd need to get user_id from username
    # For now, we'll store with username only
    # Note: Telegram usernames are unique
    
    # Create a dummy user_id based on username hash
    user_id_hash = abs(hash(username)) % 1000000
    
    if db.add_target(group_id, user_id_hash, username, target):
        await update.message.reply_text(f"✅ Target added for @{username}!\n📝 *Target:* {target}", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Failed to add target.")

async def my_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's target for today."""
    if not update.message:
        return
    
    group_id = update.message.chat.id
    user_id = update.message.from_user.id
    
    # Check if group is allowed
    if not db.is_allowed_group(group_id):
        await update.message.reply_text("🚫 This bot is not authorized to work in this group!")
        return
    
    target = db.get_today_target(user_id)
    
    if target:
        status = "✅ Completed" if target.get("completed") else "⏳ Pending"
        message = (
            f"🎯 *Your Today's Target*\n\n"
            f"📝 *Target:* {target['target']}\n"
            f"📅 *Date:* {target['date'].strftime('%Y-%m-%d')}\n"
            f"📊 *Status:* {status}\n"
            f"⏰ *Added:* {target['created_at'].strftime('%H:%M')}"
        )
        if target.get("completed_at"):
            message += f"\n✅ *Completed at:* {target['completed_at'].strftime('%H:%M')}"
    else:
        message = "📭 You haven't set a target for today!\nUse /addtarget <your target> to add one."
    
    await update.message.reply_text(message, parse_mode="Markdown")

async def today_targets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all targets for today."""
    if not update.message:
        return
    
    group_id = update.message.chat.id
    
    # Check if group is allowed
    if not db.is_allowed_group(group_id):
        await update.message.reply_text("🚫 This bot is not authorized to work in this group!")
        return
    
    targets = db.get_all_targets(group_id)
    
    if not targets:
        await update.message.reply_text("📭 No targets set for today!")
        return
    
    message = format_targets_message(targets)
    await update.message.reply_text(message, parse_mode="Markdown")

async def my_targets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's recent targets."""
    if not update.message:
        return
    
    group_id = update.message.chat.id
    user_id = update.message.from_user.id
    
    # Check if group is allowed
    if not db.is_allowed_group(group_id):
        await update.message.reply_text("🚫 This bot is not authorized to work in this group!")
        return
    
    targets = db.get_user_targets(user_id, limit=7)
    
    if not targets:
        await update.message.reply_text("📭 You haven't set any targets yet!")
        return
    
    message = "📊 *Your Recent Targets*\n\n"
    for i, target in enumerate(targets, 1):
        status = "✅" if target.get("completed") else "⏳"
        message += (
            f"{i}. {status} *{target['date'].strftime('%Y-%m-%d')}*\n"
            f"   📝 {target['target']}\n\n"
        )
    
    await update.message.reply_text(message, parse_mode="Markdown")

async def mark_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mark today's target as completed."""
    if not update.message:
        return
    
    group_id = update.message.chat.id
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    
    # Check if group is allowed
    if not db.is_allowed_group(group_id):
        await update.message.reply_text("🚫 This bot is not authorized to work in this group!")
        return
    
    target = db.get_today_target(user_id)
    
    if not target:
        await update.message.reply_text("📭 You don't have a target for today!")
        return
    
    if target.get("completed"):
        await update.message.reply_text("✅ You've already completed today's target!")
        return
    
    if db.mark_target_completed(user_id):
        await update.message.reply_text(f"🎉 Congratulations @{username}! Target marked as completed!")
    else:
        await update.message.reply_text("❌ Failed to mark target as completed.")

async def reset_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset all bot data (admin only)."""
    if not update.message:
        return
    
    # Check if user is admin
    if not await is_admin(update, context):
        await update.message.reply_text("🚫 This command is for admins only!")
        return
    
    # Create confirmation keyboard
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, reset all data", callback_data="reset_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="reset_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚠️ *WARNING: This will delete ALL bot data!*\n\n"
        "Are you sure you want to continue?",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def reset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle reset confirmation callback."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "reset_confirm":
        group_id = query.message.chat.id
        if db.reset_all_data(group_id):
            await query.edit_message_text("✅ All bot data has been reset!")
        else:
            await query.edit_message_text("❌ Failed to reset data.")
    else:
        await query.edit_message_text("Reset cancelled.")

async def bot_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot status (admin only)."""
    if not update.message:
        return
    
    # Check if user is admin
    if not await is_admin(update, context):
        await update.message.reply_text("🚫 This command is for admins only!")
        return
    
    group_id = update.message.chat.id
    allowed_group = db.get_allowed_group()
    
    if allowed_group:
        group_info = f"✅ *Authorized Group:* {allowed_group['group_name']} (ID: {allowed_group['group_id']})"
    else:
        group_info = "⚠️ *No group authorized yet*"
    
    # Count today's targets
    today_targets = db.get_all_targets(group_id)
    completed = sum(1 for t in today_targets if t.get("completed"))
    
    status_message = (
        "🤖 *Bot Status*\n\n"
        f"{group_info}\n\n"
        f"📊 *Today's Statistics:*\n"
        f"   • Total Targets: {len(today_targets)}\n"
        f"   • Completed: {completed}\n"
        f"   • Pending: {len(today_targets) - completed}\n\n"
        f"💾 *Database:* Connected\n"
        f"⚙️ *Bot Mode:* Testing"
    )
    
    await update.message.reply_text(status_message, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a help message."""
    help_text = (
        "🎯 *Target Tracker Bot Help*\n\n"
        "*User Commands:*\n"
        "📌 /addtarget <target> - Add your daily target\n"
        "📌 /mytarget - View your today's target\n"
        "📌 /today - View all targets for today\n"
        "📌 /mytargets - View your recent targets\n"
        "📌 /done - Mark your target as completed\n\n"
        "*Admin Commands:*\n"
        "🛠 /addtargetfor @username <target> - Add target for a user\n"
        "🛠 /reset - Reset all bot data\n"
        "🛠 /status - Check bot status\n"
        "🛠 /help - Show this help message\n\n"
        "*Note:* This bot only works in the authorized group!"
    )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages."""
    if not update.message:
        return
    
    # Check if message is in a group
    if update.message.chat.type in ["group", "supergroup"]:
        group_id = update.message.chat.id
        
        # Check if group is allowed
        if not db.is_allowed_group(group_id):
            # Silently ignore messages from unauthorized groups
            return
        
        # You can add additional message handling here
        # For example, reacting to certain keywords
        text = update.message.text.lower()
        
        if any(word in text for word in ["target", "goal", "task", "todo"]):
            await update.message.reply_text(
                "🎯 Don't forget to set your daily target with /addtarget !"
            )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    print(f"Update {update} caused error {context.error}")
    
    # Try to notify admin if possible
    if update and update.effective_chat:
        try:
            await update.effective_chat.send_message(
                "❌ An error occurred. Please try again later."
            )
        except:
            pass
