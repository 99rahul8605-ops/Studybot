"""
Sentence/Target management functions
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from datetime import datetime
import re

from src.database import db

async def add_sentence_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a sentence/target"""
    if not update.message:
        return
    
    group_id = update.message.chat.id
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    
    # Check if group is allowed
    if not db.is_group_allowed(group_id):
        await update.message.reply_text("🚫 This bot is not authorized to work in this group!")
        return
    
    # Check if user is verified
    if not db.is_user_verified(user_id, group_id):
        await update.message.reply_text(
            "🚫 *You need to complete registration first!*\n\n"
            "New members must:\n"
            "1. Click the registration button in group\n"
            "2. Accept declaration in DM\n"
            "3. Get unmuted automatically\n\n"
            "Once registered, you can share sentences and targets!",
            parse_mode="Markdown"
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 *Add a Sentence/Goal*\n\n"
            "Usage: `/addsentence <sentence> [category]`\n\n"
            "*Examples:*\n"
            "• `/addsentence Today I will read 50 pages`\n"
            "• `/addsentence I completed my workout #fitness`\n"
            "• `/addsentence Learning Python programming #learning`\n\n"
            "*Categories:*\n"
            "Use #hashtags for categories like: #fitness #learning #work #personal #other",
            parse_mode="Markdown"
        )
        return
    
    # Parse message
    full_text = " ".join(context.args)
    
    # Extract category (look for hashtag)
    category = "general"
    words = full_text.split()
    
    for word in words:
        if word.startswith("#"):
            category = word[1:].lower()
            full_text = full_text.replace(word, "").strip()
            break
    
    if not full_text:
        await update.message.reply_text("❌ Please provide a sentence!")
        return
    
    # Add sentence
    sentence_id = db.add_sentence(group_id, user_id, username, full_text, category)
    
    if sentence_id:
        # Create inline keyboard for like
        keyboard = [
            [
                InlineKeyboardButton("👍 Like (0)", callback_data=f"like_{sentence_id}"),
                InlineKeyboardButton("📋 My Sentences", callback_data="my_sentences")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ *Sentence Added!*\n\n"
            f"📝 *Sentence:* {full_text}\n"
            f"🏷️ *Category:* #{category}\n"
            f"👤 *By:* @{username}\n\n"
            f"Use `/sentences` to view all sentences",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("❌ Failed to add sentence. Please try again.")

# ... (rest of sentences.py remains the same)
