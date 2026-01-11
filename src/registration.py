"""
Registration module for new members
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from datetime import datetime
import re

from src.database import db

async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new member joining"""
    if not update.message or not update.message.new_chat_members:
        return
    
    group_id = update.message.chat.id
    
    # Check if group is allowed
    if not db.is_group_allowed(group_id):
        return
    
    for new_member in update.message.new_chat_members:
        # Skip if the new member is the bot itself
        if new_member.id == context.bot.id:
            continue
        
        user_id = new_member.id
        username = new_member.username or new_member.first_name
        
        print(f"👤 New member joined: {username} (ID: {user_id}) in group {group_id}")
        
        # Check if user is already verified
        if db.is_user_verified(user_id, group_id):
            print(f"✅ User {username} is already verified")
            await update.message.reply_text(
                f"👋 Welcome back @{username}! You're already verified."
            )
            return
        
        # Create registration record
        verification_code = db.create_registration(user_id, group_id, username)
        
        if not verification_code:
            await update.message.reply_text(
                f"❌ Failed to create registration for @{username}. Please contact admin."
            )
            return
        
        # Mute the user
        db.mute_user(user_id, group_id, hours=24)
        
        # Try to restrict user (requires admin permissions)
        try:
            await context.bot.restrict_chat_member(
                chat_id=group_id,
                user_id=user_id,
                permissions={
                    'can_send_messages': False,
                    'can_send_media_messages': False,
                    'can_send_polls': False,
                    'can_send_other_messages': False,
                    'can_add_web_page_previews': False,
                    'can_change_info': False,
                    'can_invite_users': False,
                    'can_pin_messages': False
                }
            )
            print(f"🔇 Muted user {username}")
        except Exception as e:
            print(f"⚠️ Could not mute user (bot needs admin): {e}")
        
        # Create registration button
        keyboard = [
            [
                InlineKeyboardButton(
                    "📝 Register Now (DM Bot)",
                    url=f"https://t.me/{context.bot.username}?start=register_{group_id}_{verification_code}"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_message = (
            f"👋 Welcome @{username} to the group!\n\n"
            "⚠️ *You need to register before you can participate.*\n\n"
            "📝 *Registration Steps:*\n"
            "1. Click the button below to open DM with bot\n"
            "2. Send the verification code to bot\n"
            "3. You'll be unmuted automatically\n\n"
            "⏰ *Time Limit:* 24 hours\n"
            "🔐 *Verification Code:* ||`{code}`||"
        ).format(code=verification_code)
        
        # Send welcome message
        try:
            await update.message.reply_text(
                welcome_message,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            
            # Try to send private message as well
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"👋 Welcome to {update.message.chat.title}!\n\n"
                        f"📝 *Registration Required*\n\n"
                        f"Your verification code: `{verification_code}`\n\n"
                        f"Send this code to me to complete registration.\n"
                        f"Or click: /verify_{verification_code}"
                    ),
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"⚠️ Could not send DM to user: {e}")
                
        except Exception as e:
            print(f"❌ Error sending welcome message: {e}")

async def handle_member_left(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle member leaving"""
    if not update.message or not update.message.left_chat_member:
        return
    
    left_member = update.message.left_chat_member
    group_id = update.message.chat.id
    
    # Skip if the left member is the bot itself
    if left_member.id == context.bot.id:
        return
    
    # User left, we can delete their registration so they need to re-register if they rejoin
    db.unmute_user(left_member.id, group_id)
    # Note: We keep registration record but mark as inactive
    registration = db.get_registration(left_member.id, group_id)
    if registration:
        db.db.registrations.update_one(
            {"user_id": left_member.id, "group_id": group_id},
            {"$set": {"status": "left_group", "left_at": datetime.now()}}
        )

async def handle_private_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command in private chat for registration"""
    if not update.message or update.message.chat.type != "private":
        return
    
    user_id = update.message.from_user.id
    
    # Check if start command has registration parameters
    if context.args and len(context.args) > 0:
        arg = context.args[0]
        
        # Check if it's a registration link
        if arg.startswith("register_"):
            try:
                parts = arg.split("_")
                if len(parts) >= 3:
                    group_id = int(parts[1])
                    code = parts[2]
                    
                    # Store in user data for verification
                    context.user_data['pending_registration'] = {
                        'group_id': group_id,
                        'code': code
                    }
                    
                    # Get group info
                    group = db.get_allowed_group()
                    group_name = group['group_name'] if group else f"Group {group_id}"
                    
                    await update.message.reply_text(
                        f"📝 *Registration for {group_name}*\n\n"
                        f"Your verification code: `{code}`\n\n"
                        "To complete registration, please:\n"
                        "1. Send me the code above\n"
                        "2. Or use command: /verify {code}\n\n"
                        "Once verified, you'll be unmuted in the group.",
                        parse_mode="Markdown"
                    )
                    return
            except (ValueError, IndexError):
                pass
    
    # Normal start in private
    await update.message.reply_text(
        "👋 Hello! I'm the Target Tracker Bot.\n\n"
        "📝 *Registration Instructions:*\n"
        "1. Join the group where I'm added\n"
        "2. Click the registration button\n"
        "3. Send me the verification code\n\n"
        "🎯 *After Registration:*\n"
        "You can set daily targets with /addtarget\n"
        "Track progress with /mytarget and /today\n\n"
        "Need help? Contact group admin."
    )

async def handle_verification_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle verification command in private chat"""
    if not update.message or update.message.chat.type != "private":
        return
    
    user_id = update.message.from_user.id
    
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide verification code.\n"
            "Usage: /verify CODE\n"
            "Or simply send me the code."
        )
        return
    
    code = context.args[0].upper().strip()
    await verify_code(update, context, code)

async def handle_verification_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle verification via regular message"""
    if not update.message or update.message.chat.type != "private":
        return
    
    text = update.message.text.strip().upper()
    
    # Check if it looks like a verification code (6 chars, alphanumeric)
    if re.match(r'^[A-Z0-9]{6}$', text):
        await verify_code(update, context, text)

async def verify_code(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    """Verify registration code"""
    user_id = update.message.from_user.id
    
    # Check pending registration from context
    pending = context.user_data.get('pending_registration')
    
    if pending:
        group_id = pending['group_id']
        expected_code = pending['code']
        
        if code == expected_code:
            # Verify registration
            if db.verify_registration(user_id, group_id, code):
                # Get group info
                group = db.get_allowed_group()
                group_name = group['group_name'] if group else f"Group {group_id}"
                
                # Unmute user in group
                try:
                    await context.bot.restrict_chat_member(
                        chat_id=group_id,
                        user_id=user_id,
                        permissions={
                            'can_send_messages': True,
                            'can_send_media_messages': True,
                            'can_send_polls': True,
                            'can_send_other_messages': True,
                            'can_add_web_page_previews': True,
                            'can_change_info': False,
                            'can_invite_users': False,
                            'can_pin_messages': False
                        }
                    )
                    
                    # Notify in group
                    username = update.message.from_user.username or update.message.from_user.first_name
                    await context.bot.send_message(
                        chat_id=group_id,
                        text=f"✅ @{username} has completed registration and is now unmuted! Welcome! 🎉"
                    )
                    
                    # Notify user
                    await update.message.reply_text(
                        f"🎉 *Registration Successful!*\n\n"
                        f"You are now verified in {group_name}.\n"
                        f"You can now participate in the group!\n\n"
                        f"🎯 *Group Features:*\n"
                        f"• Set daily targets with /addtarget\n"
                        f"• Track with /mytarget and /today\n"
                        f"• Mark completion with /done",
                        parse_mode="Markdown"
                    )
                    
                    # Clear pending registration
                    del context.user_data['pending_registration']
                    
                except Exception as e:
                    print(f"❌ Error unmuting user: {e}")
                    await update.message.reply_text(
                        "✅ Verified! But couldn't unmute you automatically.\n"
                        "Please ask admin to unmute you in the group."
                    )
            else:
                await update.message.reply_text(
                    "❌ Verification failed. Please check the code and try again."
                )
        else:
            await update.message.reply_text(
                "❌ Code doesn't match. Please use the code from your registration message."
            )
    else:
        # Search for registration with this code
        registration = db.db.registrations.find_one({
            "user_id": user_id,
            "verification_code": code,
            "status": "pending"
        })
        
        if registration:
            group_id = registration['group_id']
            if db.verify_registration(user_id, group_id, code):
                # Get group info
                group = db.get_allowed_group()
                group_name = group['group_name'] if group else f"Group {group_id}"
                
                # Unmute user in group
                try:
                    await context.bot.restrict_chat_member(
                        chat_id=group_id,
                        user_id=user_id,
                        permissions={
                            'can_send_messages': True,
                            'can_send_media_messages': True,
                            'can_send_polls': True,
                            'can_send_other_messages': True,
                            'can_add_web_page_previews': True,
                            'can_change_info': False,
                            'can_invite_users': False,
                            'can_pin_messages': False
                        }
                    )
                    
                    # Notify in group
                    username = update.message.from_user.username or update.message.from_user.first_name
                    await context.bot.send_message(
                        chat_id=group_id,
                        text=f"✅ @{username} has completed registration and is now unmuted! Welcome! 🎉"
                    )
                    
                    # Notify user
                    await update.message.reply_text(
                        f"🎉 *Registration Successful!*\n\n"
                        f"You are now verified in {group_name}.\n"
                        f"You can now participate in the group!",
                        parse_mode="Markdown"
                    )
                    
                except Exception as e:
                    print(f"❌ Error unmuting user: {e}")
                    await update.message.reply_text(
                        "✅ Verified! But couldn't unmute you automatically.\n"
                        "Please ask admin to unmute you in the group."
                    )
            else:
                await update.message.reply_text(
                    "❌ Verification failed. Please try again or contact admin."
                )
        else:
            await update.message.reply_text(
                "❌ Invalid verification code or code already used.\n"
                "Please check the code from your registration message."
            )

async def check_muted_users(context: ContextTypes.DEFAULT_TYPE):
    """Check and notify muted users (scheduled job)"""
    try:
        group = db.get_allowed_group()
        if not group:
            return
        
        group_id = group['group_id']
        muted_users = db.get_muted_users(group_id)
        
        for mute_record in muted_users:
            user_id = mute_record['user_id']
            registration = db.get_registration(user_id, group_id)
            
            if registration and registration['status'] == 'pending':
                # Calculate remaining time
                remaining = mute_record['muted_until'] - datetime.now()
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                
                if hours < 1:  # Less than 1 hour remaining
                    try:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=(
                                f"⚠️ *Registration Reminder*\n\n"
                                f"Your registration expires in {minutes} minutes!\n"
                                f"Code: `{registration['verification_code']}`\n\n"
                                f"Send the code to me or use: /verify_{registration['verification_code']}"
                            ),
                            parse_mode="Markdown"
                        )
                    except:
                        pass  # User might have blocked bot
    except Exception as e:
        print(f"Error in check_muted_users: {e}")

def setup_registration_handlers(application):
    """Setup all registration handlers"""
    # Handle new members joining
    application.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS, 
        handle_new_member
    ))
    
    # Handle members leaving
    application.add_handler(MessageHandler(
        filters.StatusUpdate.LEFT_CHAT_MEMBER, 
        handle_member_left
    ))
    
    # Handle private start command
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.Regex(r'^/start'),
        handle_private_start
    ))
    
    # Handle verification command
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.Regex(r'^/verify'),
        handle_verification_command
    ))
    
    # Handle verification via message
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
        handle_verification_message
    ))
