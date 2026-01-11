from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the user is an admin in the chat."""
    if not update.message or not update.effective_chat:
        return False
    
    try:
        user_id = update.message.from_user.id
        chat_id = update.message.chat.id
        
        # Get chat administrators
        admins = await context.bot.get_chat_administrators(chat_id)
        
        # Check if user is in admin list
        return any(admin.user.id == user_id for admin in admins)
    except Exception as e:
        print(f"Error checking admin status: {e}")
        return False

def format_targets_message(targets) -> str:
    """Format targets list into a readable message."""
    if not targets:
        return "📭 No targets set for today!"
    
    message = "🎯 *Today's Targets*\n\n"
    
    completed = []
    pending = []
    
    for target in targets:
        if target.get("completed"):
            completed.append(target)
        else:
            pending.append(target)
    
    if pending:
        message += "⏳ *Pending:*\n"
        for i, target in enumerate(pending, 1):
            message += f"{i}. @{target['username']}: {target['target']}\n"
        message += "\n"
    
    if completed:
        message += "✅ *Completed:*\n"
        for i, target in enumerate(completed, 1):
            completion_time = target.get('completed_at', datetime.now())
            if isinstance(completion_time, datetime):
                time_str = completion_time.strftime("%H:%M")
            else:
                time_str = "N/A"
            message += f"{i}. @{target['username']}: {target['target']} ({time_str})\n"
    
    total = len(targets)
    completed_count = len(completed)
    
    message += f"\n📊 *Progress:* {completed_count}/{total} completed ({int(completed_count/total*100 if total > 0 else 0)}%)"
    
    return message

def validate_target_text(text: str, max_length: int = 500) -> tuple[bool, str]:
    """Validate target text."""
    if not text or not text.strip():
        return False, "Target cannot be empty!"
    
    if len(text) > max_length:
        return False, f"Target is too long! Maximum {max_length} characters."
    
    return True, ""
