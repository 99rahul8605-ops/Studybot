"""
Main bot file - Entry point for the bot
"""
import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Start the bot."""
    # Get bot token from environment
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN environment variable is required!")
    
    print("=" * 60)
    print("🤖 Starting Target Tracker Bot")
    print("=" * 60)
    print(f"✅ Bot Token: {'✓ Set' if BOT_TOKEN else '✗ Missing'}")
    
    # Import after environment is loaded
    from src.database import db
    print(f"✅ MongoDB: {'Connected ✓' if db.client else 'Not Connected ✗'}")
    
    from src.handlers import (
        start, add_target, add_target_for_user, my_target,
        today_targets, my_targets, mark_done, reset_data,
        reset_callback, bot_status, help_command,
        handle_group_message, error_handler
    )
    from src.registration import setup_registration_handlers, check_muted_users
    from src.sentences import setup_sentence_handlers
    
    # Create Application
    application = Application.builder().token(BOT_TOKEN).build()
    print("✅ Application created")
    
    # Get bot info
    bot = application.bot
    print(f"🤖 Bot Username: @{bot.username}")
    print(f"🤖 Bot Name: {bot.first_name}")
    
    # Register command handlers for groups
    application.add_handler(CommandHandler("start", start, filters=filters.ChatType.GROUP | filters.ChatType.SUPERGROUP))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("addtarget", add_target))
    application.add_handler(CommandHandler("addtargetfor", add_target_for_user))
    application.add_handler(CommandHandler("mytarget", my_target))
    application.add_handler(CommandHandler("today", today_targets))
    application.add_handler(CommandHandler("mytargets", my_targets))
    application.add_handler(CommandHandler("done", mark_done))
    application.add_handler(CommandHandler("reset", reset_data))
    application.add_handler(CommandHandler("status", bot_status))
    
    # Register callback handler for reset confirmation
    application.add_handler(CallbackQueryHandler(reset_callback, pattern="^reset_"))
    
    # Register message handler for groups
    application.add_handler(MessageHandler(filters.ChatType.GROUP & filters.TEXT & ~filters.COMMAND, handle_group_message))
    
    # Setup registration handlers
    print("🔄 Setting up registration handlers...")
    setup_registration_handlers(application)
    
    # Setup sentence handlers
    print("🔄 Setting up sentence handlers...")
    setup_sentence_handlers(application)
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Setup job queue for checking muted users
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(check_muted_users, interval=1800, first=10)
        print("✅ Scheduled job for muted users check")
    
    # Get allowed group info
    allowed_group = db.get_allowed_group()
    if allowed_group:
        print(f"✅ Authorized Group: {allowed_group['group_name']} (ID: {allowed_group['group_id']})")
    else:
        print("⚠️ No group authorized yet. Bot will work in the first group it's added to.")
    
    print("=" * 60)
    print("📋 Bot Features:")
    print("  ✅ New member auto-mute")
    print("  ✅ Registration via DM with inline buttons")
    print("  ✅ Declaration acceptance system")
    print("  ✅ Auto-unmute after registration")
    print("  ✅ Target tracking system")
    print("  ✅ Sentence sharing with categories")
    print("=" * 60)
    print("🔧 Important Requirements:")
    print("  1. Bot MUST be admin in the group")
    print("  2. Bot needs these admin permissions:")
    print("     • Delete messages")
    print("     • Restrict members")
    print("     • Ban members")
    print("=" * 60)
    print("📝 Registration URL Format:")
    print(f"  https://t.me/{bot.username}?start=register_GROUP_ID")
    print("=" * 60)
    print("🚀 Bot is starting...")
    
    # Run the bot
    application.run_polling(allowed_updates=None, drop_pending_updates=True)


if __name__ == '__main__':
    main()
