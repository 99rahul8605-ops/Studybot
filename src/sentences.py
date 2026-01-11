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
        await update.message.reply_text("🚫 You need to complete registration first!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 *Add a Sentence/Target*\n\n"
            "Usage: `/addsentence <sentence> [category]`\n\n"
            "*Examples:*\n"
            "• `/addsentence Today I will read 50 pages`\n"
            "• `/addsentence I completed my workout #fitness`\n"
            "• `/addsentence Learning Python programming #learning`\n\n"
            "*Categories:*\n"
            "• #fitness\n• #learning\n• #work\n• #personal\n• #other",
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

async def show_sentences_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent sentences"""
    if not update.message:
        return
    
    group_id = update.message.chat.id
    
    # Check if group is allowed
    if not db.is_group_allowed(group_id):
        await update.message.reply_text("🚫 This bot is not authorized to work in this group!")
        return
    
    # Get category from args if provided
    category = None
    if context.args:
        category_arg = context.args[0].lower()
        if category_arg.startswith("#"):
            category = category_arg[1:]
        else:
            category = category_arg
    
    # Get sentences
    sentences = db.get_group_sentences(group_id, category, limit=10)
    
    if not sentences:
        if category:
            await update.message.reply_text(f"📭 No sentences found in category #{category}")
        else:
            await update.message.reply_text("📭 No sentences added yet!")
        return
    
    # Get categories
    categories = db.get_sentence_categories(group_id)
    
    # Create category buttons
    category_buttons = []
    row = []
    for cat in categories[:5]:  # Show top 5 categories
        row.append(InlineKeyboardButton(f"#{cat['name']} ({cat['count']})", callback_data=f"cat_{cat['name']}"))
        if len(row) == 2:  # 2 buttons per row
            category_buttons.append(row)
            row = []
    if row:
        category_buttons.append(row)
    
    category_buttons.append([
        InlineKeyboardButton("📋 All Categories", callback_data="cat_all"),
        InlineKeyboardButton("➕ Add Sentence", callback_data="add_sentence_btn")
    ])
    
    reply_markup = InlineKeyboardMarkup(category_buttons)
    
    # Format message
    message = f"📚 *Recent Sentences*"
    if category:
        message += f" (Category: #{category})"
    message += "\n\n"
    
    for i, sentence in enumerate(sentences, 1):
        time_ago = (datetime.now() - sentence['created_at']).seconds // 60
        if time_ago < 60:
            time_str = f"{time_ago}m ago"
        else:
            time_str = sentence['created_at'].strftime("%H:%M")
        
        message += (
            f"{i}. *{sentence['sentence']}*\n"
            f"   👤 @{sentence['username']} • 👍 {sentence.get('likes', 0)} • 🏷️ #{sentence.get('category', 'general')}\n"
            f"   ⏰ {time_str}\n\n"
        )
    
    await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)

async def my_sentences_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's sentences"""
    if not update.message:
        return
    
    group_id = update.message.chat.id
    user_id = update.message.from_user.id
    
    # Check if group is allowed
    if not db.is_group_allowed(group_id):
        await update.message.reply_text("🚫 This bot is not authorized to work in this group!")
        return
    
    # Check if user is verified
    if not db.is_user_verified(user_id, group_id):
        await update.message.reply_text("🚫 You need to complete registration first!")
        return
    
    # Get sentences
    sentences = db.get_user_sentences(user_id, group_id, limit=10)
    
    if not sentences:
        await update.message.reply_text(
            "📭 You haven't added any sentences yet!\n\n"
            "Use `/addsentence <your sentence>` to add one.",
            parse_mode="Markdown"
        )
        return
    
    message = "📝 *Your Sentences*\n\n"
    
    for i, sentence in enumerate(sentences, 1):
        time_ago = (datetime.now() - sentence['created_at']).seconds // 60
        if time_ago < 60:
            time_str = f"{time_ago}m ago"
        else:
            time_str = sentence['created_at'].strftime("%H:%M")
        
        message += (
            f"{i}. *{sentence['sentence']}*\n"
            f"   👍 {sentence.get('likes', 0)} likes • 🏷️ #{sentence.get('category', 'general')}\n"
            f"   ⏰ {time_str}\n\n"
        )
    
    keyboard = [
        [
            InlineKeyboardButton("➕ Add New Sentence", callback_data="add_sentence_btn"),
            InlineKeyboardButton("📚 All Sentences", callback_data="show_sentences_btn")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)

async def like_sentence_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle like button callback"""
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith("like_"):
        return
    
    sentence_id = query.data.split("_")[1]
    user_id = query.from_user.id
    
    # Like/unlike sentence
    success = db.like_sentence(sentence_id, user_id)
    
    if success:
        # Update button text
        sentence = db.db.sentences.find_one({"_id": sentence_id})
        if sentence:
            like_count = sentence.get("likes", 0)
            
            # Update button
            keyboard = query.message.reply_markup.inline_keyboard
            new_keyboard = []
            
            for row in keyboard:
                new_row = []
                for button in row:
                    if button.callback_data == query.data:
                        new_row.append(InlineKeyboardButton(
                            f"👍 Like ({like_count})",
                            callback_data=button.callback_data
                        ))
                    else:
                        new_row.append(button)
                new_keyboard.append(new_row)
            
            reply_markup = InlineKeyboardMarkup(new_keyboard)
            
            # Edit message
            await query.edit_message_reply_markup(reply_markup=reply_markup)
    else:
        await query.answer("❌ Failed to like sentence", show_alert=True)

async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle category filter callback"""
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith("cat_"):
        return
    
    category = query.data.split("_", 1)[1]
    group_id = query.message.chat.id
    
    # Get sentences for category
    if category == "all":
        sentences = db.get_group_sentences(group_id, limit=10)
        category_name = "All Categories"
    else:
        sentences = db.get_group_sentences(group_id, category, limit=10)
        category_name = f"#{category}"
    
    if not sentences:
        await query.answer(f"No sentences in {category_name}", show_alert=True)
        return
    
    # Get categories
    categories = db.get_sentence_categories(group_id)
    
    # Create category buttons
    category_buttons = []
    row = []
    for cat in categories[:5]:
        row.append(InlineKeyboardButton(f"#{cat['name']} ({cat['count']})", callback_data=f"cat_{cat['name']}"))
        if len(row) == 2:
            category_buttons.append(row)
            row = []
    if row:
        category_buttons.append(row)
    
    category_buttons.append([
        InlineKeyboardButton("📋 All Categories", callback_data="cat_all"),
        InlineKeyboardButton("➕ Add Sentence", callback_data="add_sentence_btn")
    ])
    
    reply_markup = InlineKeyboardMarkup(category_buttons)
    
    # Format message
    message = f"📚 *Sentences - {category_name}*\n\n"
    
    for i, sentence in enumerate(sentences, 1):
        time_ago = (datetime.now() - sentence['created_at']).seconds // 60
        if time_ago < 60:
            time_str = f"{time_ago}m ago"
        else:
            time_str = sentence['created_at'].strftime("%H:%M")
        
        message += (
            f"{i}. *{sentence['sentence']}*\n"
            f"   👤 @{sentence['username']} • 👍 {sentence.get('likes', 0)} • 🏷️ #{sentence.get('category', 'general')}\n"
            f"   ⏰ {time_str}\n\n"
        )
    
    await query.edit_message_text(message, parse_mode="Markdown", reply_markup=reply_markup)

async def add_sentence_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle add sentence button callback"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📝 *Add a Sentence*\n\n"
        "Use the command:\n"
        "`/addsentence <your sentence> [category]`\n\n"
        "*Examples:*\n"
        "• `/addsentence Today I will read 50 pages`\n"
        "• `/addsentence I completed my workout #fitness`\n"
        "• `/addsentence Learning Python programming #learning`",
        parse_mode="Markdown"
    )

async def my_sentences_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle my sentences button callback"""
    query = update.callback_query
    await query.answer()
    
    # Get user sentences
    group_id = query.message.chat.id
    user_id = query.from_user.id
    
    sentences = db.get_user_sentences(user_id, group_id, limit=10)
    
    if not sentences:
        await query.edit_message_text(
            "📭 You haven't added any sentences yet!\n\n"
            "Use `/addsentence <your sentence>` to add one.",
            parse_mode="Markdown"
        )
        return
    
    message = "📝 *Your Sentences*\n\n"
    
    for i, sentence in enumerate(sentences, 1):
        time_ago = (datetime.now() - sentence['created_at']).seconds // 60
        if time_ago < 60:
            time_str = f"{time_ago}m ago"
        else:
            time_str = sentence['created_at'].strftime("%H:%M")
        
        message += (
            f"{i}. *{sentence['sentence']}*\n"
            f"   👍 {sentence.get('likes', 0)} likes • 🏷️ #{sentence.get('category', 'general')}\n"
            f"   ⏰ {time_str}\n\n"
        )
    
    keyboard = [
        [
            InlineKeyboardButton("➕ Add New Sentence", callback_data="add_sentence_btn"),
            InlineKeyboardButton("📚 All Sentences", callback_data="show_sentences_btn")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, parse_mode="Markdown", reply_markup=reply_markup)

async def show_sentences_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle show sentences button callback"""
    query = update.callback_query
    await query.answer()
    
    # Redirect to show_sentences_command logic
    update.message = query.message
    context.args = []
    await show_sentences_command(update, context)

def setup_sentence_handlers(application):
    """Setup sentence handlers"""
    # Add sentence command
    application.add_handler(CommandHandler("addsentence", add_sentence_command))
    application.add_handler(CommandHandler("addtargetsentence", add_sentence_command))  # Alias
    
    # Show sentences command
    application.add_handler(CommandHandler("sentences", show_sentences_command))
    application.add_handler(CommandHandler("targetsentences", show_sentences_command))  # Alias
    
    # My sentences command
    application.add_handler(CommandHandler("mysentences", my_sentences_command))
    application.add_handler(CommandHandler("mytargetsentences", my_sentences_command))  # Alias
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(like_sentence_callback, pattern="^like_"))
    application.add_handler(CallbackQueryHandler(category_callback, pattern="^cat_"))
    application.add_handler(CallbackQueryHandler(add_sentence_button_callback, pattern="^add_sentence_btn$"))
    application.add_handler(CallbackQueryHandler(my_sentences_button_callback, pattern="^my_sentences$"))
    application.add_handler(CallbackQueryHandler(show_sentences_button_callback, pattern="^show_sentences_btn$"))
