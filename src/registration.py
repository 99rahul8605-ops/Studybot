"""
Registration module for new members with declaration acceptance
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from datetime import datetime
import re
import json

from src.database import db

# Conversation states for declaration flow
DECLARATION, ACCEPT_DECLARATION = range(2)

# Declaration text that users must accept
DECLARATION_TEXT = """📋 *GROUP DECLARATION & RULES*

By joining this group, you agree to:

1. ✅ Respect all members
2. ✅ No spam or self-promotion
3. ✅ Stay on topic
4. ✅ Use appropriate language
5. ✅ Follow admin instructions
6. ✅ Set daily targets and track progress
7. ✅ Participate actively in group activities

*Do you accept these rules and declare to follow them?*

Type "YES, I ACCEPT" to continue.
"""

async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new member joining with declaration system"""
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
            continue
        
        # Create registration record
        registration_id = db.create_registration(user_id, group_id, username)
        
        if not registration_id:
            await update.message.reply_text(
                f"❌ Failed to create registration for @{username}. Please contact admin."
            )
            continue
        
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
                    "📝 Complete Registration (DM Bot)",
                    url=f"https://t.me/{context.bot.username}?start=register_{group_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "📋 View Group Rules",
                    callback_data=f"view_rules_{user_id}"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_message = (
            f"👋 Welcome @{username} to the group!\n\n"
            "⚠️ *REGISTRATION REQUIRED*\n\n"
            "📝 *Before participating, you must:*\n"
            "1. Read and accept group declaration\n"
            "2. Complete registration via DM with bot\n"
            "3. You'll be unmuted automatically\n\n"
            "⏰ *Time Limit:* 24 hours\n"
            "🔐 *Click the button below to start*\n\n"
            "❓ *Why registration?*\n"
            "To ensure all members agree to group rules and maintain quality discussions."
        )
        
        # Send welcome message
        try:
            await update.message.reply_text(
                welcome_message,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            print(f"❌ Error sending welcome message: {e}")

async def view_rules_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback for viewing rules"""
    query = update.callback_query
    await query.answer()
    
    # Extract user_id from callback data
    try:
        user_id = int(query.data.split('_')[-1])
    except:
        user_id = query.from_user.id
    
    await query.edit_message_text(
        DECLARATION_TEXT,
        parse_mode="Markdown"
    )

async def handle_private_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command in private chat for registration"""
    if not update.message or update.message.chat.type != "private":
        return
    
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    
    # Check if start command has registration parameters
    if context.args and len(context.args) > 0:
        arg = context.args[0]
        
        # Check if it's a registration link
        if arg.startswith("register_"):
            try:
                group_id = int(arg.split("_")[1])
                
                # Check if user is in this group
                try:
                    chat_member = await context.bot.get_chat_member(group_id, user_id)
                    if chat_member.status not in ['member', 'administrator', 'creator']:
                        await update.message.reply_text(
                            "❌ You must be a member of the group to register.\n"
                            "Please join the group first and try again."
                        )
                        return
                except:
                    await update.message.reply_text(
                        "❌ You must be a member of the group to register.\n"
                        "Please join the group first and try again."
                    )
                    return
                
                # Check if user is already verified
                if db.is_user_verified(user_id, group_id):
                    await update.message.reply_text(
                        "✅ You are already verified in this group!\n"
                        "You can now participate in discussions."
                    )
                    return
                
                # Check if user has pending registration
                registration = db.get_registration(user_id, group_id)
                if not registration:
                    await update.message.reply_text(
                        "❌ No registration found. Please use the registration button in the group."
                    )
                    return
                
                # Store registration info in context
                context.user_data['registration'] = {
                    'group_id': group_id,
                    'user_id': user_id,
                    'username': username
                }
                
                # Send declaration
                await update.message.reply_text(
                    DECLARATION_TEXT + "\n\n"
                    "*Please type exactly:* `YES, I ACCEPT`",
                    parse_mode="Markdown"
                )
                
                return DECLARATION
                
            except (ValueError, IndexError) as e:
                print(f"Error parsing registration link: {e}")
    
    # Normal start in private
    await update.message.reply_text(
        "👋 Hello! I'm the Target Tracker Bot.\n\n"
        "📝 *Registration Instructions:*\n"
        "1. Join the group where I'm added\n"
        "2. Click the registration button in the group\n"
        "3. Read and accept the declaration in DM\n"
        "4. You'll be automatically unmuted\n\n"
        "🎯 *After Registration:*\n"
        "You can set daily targets with /addtarget\n"
        "Track progress with /mytarget and /today\n\n"
        "Need help? Contact group admin."
    )
    return ConversationHandler.END

async def handle_declaration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle declaration acceptance"""
    if not update.message or update.message.chat.type != "private":
        return DECLARATION
    
    text = update.message.text.strip().upper()
    
    if text == "YES, I ACCEPT":
        # Get registration info
        registration_info = context.user_data.get('registration')
        if not registration_info:
            await update.message.reply_text(
                "❌ Registration session expired. Please start again from the group."
            )
            return ConversationHandler.END
        
        user_id = registration_info['user_id']
        group_id = registration_info['group_id']
        username = registration_info['username']
        
        # Verify registration
        registration = db.get_registration(user_id, group_id)
        if not registration:
            await update.message.reply_text(
                "❌ Registration not found. Please use the registration button in the group."
            )
            return ConversationHandler.END
        
        # Update registration status
        db.verify_registration(user_id, group_id)
        
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
            
            # Get group info
            group_info = await context.bot.get_chat(group_id)
            group_name = group_info.title if hasattr(group_info, 'title') else f"Group {group_id}"
            
            # Notify in group
            await context.bot.send_message(
                chat_id=group_id,
                text=f"🎉 *WELCOME @{username}!*\n\n"
                     f"✅ Has accepted the group declaration\n"
                     f"✅ Is now a verified member\n"
                     f"✅ Can participate in discussions\n\n"
                     f"*Reminder:* Don't forget to set your daily target with /addtarget !",
                parse_mode="Markdown"
            )
            
            # Notify user
            await update.message.reply_text(
                f"🎉 *REGISTRATION SUCCESSFUL!*\n\n"
                f"✅ Declaration accepted\n"
                f"✅ You are now verified in *{group_name}*\n"
                f"✅ You have been unmuted in the group\n\n"
                f"*Next Steps:*\n"
                f"1. Return to the group\n"
                f"2. Set your daily target: /addtarget\n"
                f"3. Check others' targets: /today\n"
                f"4. Mark completed: /done\n\n"
                f"📊 *Track your progress with:*\n"
                f"• /mytarget - View your target\n"
                f"• /mytargets - View your history\n"
                f"• /today - View all targets\n\n"
                f"Welcome to the community! 🎯",
                parse_mode="Markdown"
            )
            
        except Exception as e:
            print(f"❌ Error unmuting user: {e}")
            await update.message.reply_text(
                "✅ Declaration accepted!\n"
                "But I couldn't unmute you automatically.\n"
                "Please ask an admin to unmute you in the group."
            )
        
        # Clear registration data
        if 'registration' in context.user_data:
            del context.user_data['registration']
        
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "❌ *Incorrect response.*\n\n"
            "Please type exactly: `YES, I ACCEPT`\n\n"
            "If you don't agree with the declaration, you cannot participate in the group.",
            parse_mode="Markdown"
        )
        return DECLARATION

async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the registration process"""
    await update.message.reply_text(
        "❌ Registration cancelled.\n"
        "You can start again by clicking the registration button in the group."
    )
    
    # Clear registration data
    if 'registration' in context.user_data:
        del context.user_data['registration']
    
    return ConversationHandler.END

async def handle_member_left(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle member leaving"""
    if not update.message or not update.message.left_chat_member:
        return
    
    left_member = update.message.left_chat_member
    group_id = update.message.chat.id
    
    # Skip if the left member is the bot itself
    if left_member.id == context.bot.id:
        return
    
    # User left, mark registration as inactive
    db.unmute_user(left_member.id, group_id)
    
    # Update registration status
    registration = db.get_registration(left_member.id, group_id)
    if registration:
        db.db.registrations.update_one(
            {"user_id": left_member.id, "group_id": group_id},
            {"$set": {"status": "left_group", "left_at": datetime.now()}}
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
                                f"⚠️ *REGISTRATION REMINDER*\n\n"
                                f"Your registration expires in {minutes} minutes!\n\n"
                                f"To complete registration:\n"
                                f"1. Click the registration button in the group\n"
                                f"2. Read and accept the declaration in DM\n\n"
                                f"*Note:* If you don't register in time, you'll be removed from the group."
                            ),
                            parse_mode="Markdown"
                        )
                    except:
                        pass  # User might have blocked bot
    except Exception as e:
        print(f"Error in check_muted_users: {e}")

def setup_registration_handlers(application):
    """Setup all registration handlers"""
    
    # Conversation handler for registration
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.ChatType.PRIVATE & filters.Regex(r'^/start'),
                handle_private_start
            )
        ],
        states={
            DECLARATION: [
                MessageHandler(
                    filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
                    handle_declaration
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_registration),
            MessageHandler(filters.COMMAND, cancel_registration)
        ],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)
    
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
    
    # Callback for viewing rules
    application.add_handler(CallbackQueryHandler(
        view_rules_callback,
        pattern="^view_rules_"
    ))
