import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update

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
        raise ValueError("❌ BOT_TOKEN environment variable is required! Please add it to your .env file or environment variables.")
    
    # Import handlers after environment is loaded
    from src.database import db
    from src.handlers import (
        start, add_target, add_target_for_user, my_target,
        today_targets, my_targets, mark_done, reset_data,
        reset_callback, bot_status, help_command,
        handle_message, error_handler
    )
    
    # Create Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
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
    
    # Register message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Start the Bot
    print("=" * 50)
    print("🤖 Starting Target Tracker Bot...")
    print(f"✅ Bot Token: {'✓' if BOT_TOKEN else '✗'}")
    print(f"✅ MongoDB: {'Connected ✓' if db.client else 'Not Connected ✗'}")
    
    # Get allowed group info
    allowed_group = db.get_allowed_group()
    if allowed_group:
        print(f"✅ Authorized Group: {allowed_group['group_name']} (ID: {allowed_group['group_id']})")
    else:
        print("⚠️ No group authorized yet. Bot will work in the first group it's added to.")
    print("=" * 50)
    print("📋 Available Commands:")
    print("  /start - Start the bot")
    print("  /addtarget <target> - Add your daily target")
    print("  /mytarget - View your today's target")
    print("  /today - View all targets for today")
    print("  /mytargets - View your recent targets")
    print("  /done - Mark target as completed")
    print("  /reset - Reset all data (admin)")
    print("  /status - Check bot status (admin)")
    print("=" * 50)
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()
