"""
Registration module for new members with inline button declaration acceptance
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, CommandHandler
from datetime import datetime, timedelta
import logging

from src.database import db

# Set up logging
logger = logging.getLogger(__name__)

# Declaration text that users must accept
DECLARATION_TEXT = """📋 *GROUP DECLARATION & RULES*

By joining this group, you agree to:

1. ✅ *Respect All Members* - Be kind and respectful to everyone
2. ✅ *No Spam or Self-Promotion* - Keep content relevant and valuable
3. ✅ *Stay On Topic* - Focus on group goals and discussions
4. ✅ *Use Appropriate Language* - Maintain professional communication
5. ✅ *Follow Admin Instructions* - Cooperate with group moderators
6. ✅ *Set Daily Targets* - Actively participate in goal tracking
7. ✅ *Participate Actively* - Engage in group activities and discussions
8. ✅ *Confidentiality* - Keep group discussions within the group

*Violation of these rules may result in removal from the group.*
"""


async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new member joining - Mute them and ask for registration"""
    if not update.message or not update.message.new_chat_members:
        return
    
    group_id = update.message.chat.id
    print(f"👥 New member event in group {group_id}")
    
    # Check if group is allowed
    if not db.is_group_allowed(group_id):
        print(f"❌ Group {group_id} not allowed")
        return
    
    for new_member in update.message.new_chat_members:
        # Skip if the new member is the bot itself
        if new_member.id == context.bot.id:
            continue
        
        user_id = new_member.id
        username = new_member.username or new_member.first_name
        
        print(f"👤 New member: {username} (ID: {user_id}) in group {group_id}")
        
        # Check if user is already verified
        if db.is_user_verified(user_id, group_id):
            print(f"✅ User {username} is already verified")
            await update.message.reply_text(
                f"👋 Welcome back @{username}! You're already verified."
            )
            continue
        
        # Create registration record
        registration_success = db.create_registration(user_id, group_id, username)
        
        if not registration_success:
            print(f"❌ Failed to create registration for {username}")
            await update.message.reply_text(
                f"❌ Failed to create registration for @{username}. Please contact admin."
            )
            continue
        
        print(f"📝 Created registration record for {username}")
        
        # Mute the user permanently (until they register)
        db.mute_user(user_id, group_id)
        print(f"🔇 Permanently muted user {username} until registration")
        
        # Try to restrict user permanently (requires admin permissions)
        try:
            # Restrict user permanently (no until_date = permanent)
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
                # No until_date = permanent restriction
            )
            print(f"✅ Successfully restricted user {username} permanently")
        except Exception as e:
            print(f"⚠️ Could not restrict user (bot needs admin): {e}")
            await update.message.reply_text(
                "⚠️ *Bot Warning:* I need admin permissions to mute new members!\n"
                "Please make me an admin with:\n"
                "• Delete messages\n"
                "• Restrict members\n"
                "• Ban members",
                parse_mode="Markdown"
            )
            continue
        
        # Get bot username safely
        try:
            bot_info = await context.bot.get_me()
            bot_username = bot_info.username
            registration_link = f"https://t.me/{bot_username}?start=register_{group_id}"
            print(f"🔗 Registration link: {registration_link}")
        except Exception as e:
            print(f"❌ Could not get bot username: {e}")
            # Fallback: user will need to start the bot manually
            registration_link = f"https://t.me/{context.bot.username}?start=register_{group_id}" if context.bot.username else None
        
        if not registration_link:
            await update.message.reply_text(
                f"👋 Welcome @{username}!\n\n"
                "⚠️ Please start a chat with me (DM) and send:\n"
                f"/start register_{group_id}\n\n"
                "To complete registration."
            )
            return
        
        # Create registration button
        keyboard = [
            [
                InlineKeyboardButton(
                    "📝 Complete Registration (DM Bot)",
                    url=registration_link
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
            "1. Click the button below to open DM with bot\n"
            "2. Read and accept the group declaration\n"
            "3. You'll be automatically unmuted\n\n"
            "🔒 *Important:* You will remain muted until you complete registration.\n"
            "🔐 *Click the button below to start registration*"
        )
        
        # Send welcome message
        try:
            await update.message.reply_text(
                welcome_message,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            print(f"✅ Sent welcome message to {username}")
            
        except Exception as e:
            print(f"❌ Error sending welcome message: {e}")


async def view_rules_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback for viewing rules in group"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        DECLARATION_TEXT + "\n\n" +
        "📌 *To complete registration:*\n"
        "1. Click 'Complete Registration' button\n"
        "2. You'll be redirected to bot DM\n"
        "3. Accept declaration with inline button\n"
        "4. You'll be automatically unmuted",
        parse_mode="Markdown"
    )


async def handle_private_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command in private chat for registration"""
    if not update.message or update.message.chat.type != "private":
        return
    
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    
    print(f"🔑 Private /start from {username} (ID: {user_id})")
    
    # Check if start command has registration parameters
    if context.args and len(context.args) > 0:
        arg = context.args[0]
        
        # Check if it's a registration link
        if arg.startswith("register_"):
            try:
                group_id = int(arg.split("_")[1])
                print(f"📝 Registration attempt for group {group_id} by {username}")
                
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
                        "❌ No pending registration found.\n\n"
                        "*Possible reasons:*\n"
                        "• Registration link expired\n"
                        "• You already completed registration\n"
                        "• You need to click the registration button in the group again\n\n"
                        "Please return to the group and click the registration button.",
                        parse_mode="Markdown"
                    )
                    return
                
                # Check if registration is still pending
                if registration.get('status') != 'pending':
                    await update.message.reply_text(
                        f"❌ Your registration status is: {registration.get('status', 'unknown')}\n"
                        "Please use the registration button in the group again."
                    )
                    return
                
                # Store registration info in context
                context.user_data['registration'] = {
                    'group_id': group_id,
                    'user_id': user_id,
                    'username': username
                }
                
                print(f"📋 Showing declaration to {username} for group {group_id}")
                
                # Send declaration with inline buttons
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "✅ I ACCEPT THE DECLARATION",
                            callback_data=f"accept_declaration_{group_id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "❌ I DECLINE",
                            callback_data=f"decline_declaration_{group_id}"
                        )
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    DECLARATION_TEXT + "\n\n" +
                    "*Please read the declaration carefully and click one of the buttons below:*",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
                
                return
                
            except (ValueError, IndexError) as e:
                print(f"❌ Error parsing registration link: {e}")
                await update.message.reply_text(
                    "❌ Invalid registration link. Please use the registration button in the group."
                )
                return
    
    # Normal start in private (not a registration link)
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


async def handle_accept_declaration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle declaration acceptance via inline button"""
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith("accept_declaration_"):
        return
    
    try:
        group_id = int(query.data.split("_")[-1])
        user_id = query.from_user.id
        username = query.from_user.username or query.from_user.first_name
        
        print(f"✅ User {username} accepting declaration for group {group_id}")
        
        # Check if registration exists
        registration = db.get_registration(user_id, group_id)
        if not registration:
            await query.edit_message_text(
                "❌ Registration not found or expired.\n"
                "Please use the registration button in the group again."
            )
            return
        
        # Check if registration is still pending
        if registration.get('status') != 'pending':
            await query.edit_message_text(
                f"❌ Registration status is already: {registration.get('status', 'unknown')}\n"
                "You cannot accept the declaration again."
            )
            return
        
        # Verify registration
        success = db.verify_registration(user_id, group_id)
        print(f"✅ Verified registration for {username}: {success}")
        
        # Try to get group info
        try:
            group_info = await context.bot.get_chat(group_id)
            group_name = group_info.title if hasattr(group_info, 'title') else f"Group {group_id}"
        except:
            group_name = f"Group {group_id}"
        
        # Try to unmute user in group
        try:
            # Remove restrictions
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
            print(f"✅ Unmuted user {username} in group {group_id}")
            
            # Update message in DM
            await query.edit_message_text(
                f"🎉 *REGISTRATION SUCCESSFUL!*\n\n"
                f"✅ Declaration accepted\n"
                f"✅ You are now verified in *{group_name}*\n"
                f"✅ You have been unmuted in the group\n\n"
                f"*Next Steps:*\n"
                f"1. Return to the group\n"
                f"2. Set your daily target: `/addtarget <your target>`\n"
                f"3. Check others' targets: `/today`\n"
                f"4. Mark completed: `/done`\n\n"
                f"📊 *Track your progress with:*\n"
                f"• `/mytarget` - View your target\n"
                f"• `/mytargets` - View your history\n"
                f"• `/sentences` - View all targets/sentences\n\n"
                f"*Welcome to the community!* 🎯",
                parse_mode="Markdown"
            )
            
            # Notify in group
            try:
                await context.bot.send_message(
                    chat_id=group_id,
                    text=f"🎉 *WELCOME @{username}!*\n\n"
                         f"✅ Has accepted the group declaration\n"
                         f"✅ Is now a verified member\n"
                         f"✅ Can participate in discussions\n\n"
                         f"*Reminder:* Don't forget to set your daily target with `/addtarget` !",
                    parse_mode="Markdown"
                )
                print(f"✅ Sent welcome announcement for {username} in group")
            except Exception as e:
                print(f"⚠️ Could not send welcome message in group: {e}")
            
            # Clear registration data from user_data
            if 'registration' in context.user_data:
                del context.user_data['registration']
                
        except Exception as e:
            print(f"❌ Error unmuting user: {e}")
            # Still update registration status even if unmute fails
            await query.edit_message_text(
                f"✅ Declaration accepted!\n"
                f"✅ You are now verified in *{group_name}*\n\n"
                f"⚠️ *Note:* I couldn't unmute you automatically (bot might not be admin).\n"
                f"Please ask an admin to unmute you in the group.\n\n"
                f"Once unmuted, you can:\n"
                f"• Set targets with `/addtarget`\n"
                f"• Track progress with `/today`\n"
                f"• Share sentences with `/addsentence`",
                parse_mode="Markdown"
            )
    
    except (ValueError, IndexError) as e:
        print(f"❌ Error processing acceptance: {e}")
        await query.answer("❌ Error processing your acceptance", show_alert=True)


async def handle_decline_declaration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle declaration decline via inline button"""
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith("decline_declaration_"):
        return
    
    try:
        group_id = int(query.data.split("_")[-1])
        user_id = query.from_user.id
        
        # Remove registration record
        db.db.registrations.delete_one({"user_id": user_id, "group_id": group_id})
        
        # Also remove mute record
        db.unmute_user(user_id, group_id)
        
        await query.edit_message_text(
            "❌ *Registration Declined*\n\n"
            "You have chosen not to accept the group declaration.\n"
            "As a result, you will remain muted in the group.\n\n"
            "If you change your mind, you can:\n"
            "1. Click the registration button in the group again\n"
            "2. Re-read the declaration\n"
            "3. Accept to join the community\n\n"
            "Thank you for your time!",
            parse_mode="Markdown"
        )
        print(f"❌ User {user_id} declined declaration for group {group_id}")
    
    except Exception as e:
        print(f"Error processing decline: {e}")


async def handle_member_left(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle member leaving"""
    if not update.message or not update.message.left_chat_member:
        return
    
    left_member = update.message.left_chat_member
    group_id = update.message.chat.id
    
    # Skip if the left member is the bot itself
    if left_member.id == context.bot.id:
        return
    
    # User left, remove mute record
    db.unmute_user(left_member.id, group_id)
    
    # Update registration status
    registration = db.get_registration(left_member.id, group_id)
    if registration:
        db.db.registrations.update_one(
            {"user_id": left_member.id, "group_id": group_id},
            {"$set": {"status": "left_group", "left_at": datetime.now()}}
        )
    
    print(f"👋 User {left_member.username or left_member.first_name} left group {group_id}")


async def check_muted_users(context: ContextTypes.DEFAULT_TYPE):
    """Check and notify muted users (scheduled job)"""
    try:
        group = db.get_allowed_group()
        if not group:
            return
        
        group_id = group['group_id']
        pending_registrations = db.get_pending_registrations(group_id)
        
        for registration in pending_registrations:
            user_id = registration['user_id']
            username = registration.get('username', f"User_{user_id}")
            
            # Calculate time since registration
            time_since_registration = datetime.now() - registration['created_at']
            hours = int(time_since_registration.total_seconds() // 3600)
            minutes = int((time_since_registration.total_seconds() % 3600) // 60)
            
            # Send reminders at specific intervals
            reminder_sent = False
            
            # First 24 hours: reminders at 1, 6, 12, 18, 23 hours
            if hours < 24:
                if hours in [1, 6, 12, 18, 23]:
                    reminder_text = (
                        f"⏰ *REGISTRATION REMINDER*\n\n"
                        f"You've been in the group for {hours} hours.\n\n"
                        f"*To complete registration:*\n"
                        f"1. Click the registration button in the group\n"
                        f"2. Read and accept the declaration in DM\n\n"
                        f"*Note:* You will remain muted until you register."
                    )
                    reminder_sent = True
            # After 24 hours: reminders every 12 hours
            else:
                # Send reminder every 12 hours
                if hours % 12 == 0:
                    reminder_text = (
                        f"⏰ *REGISTRATION REMINDER*\n\n"
                        f"You've been in the group for {hours} hours.\n"
                        f"You are still muted until you complete registration.\n\n"
                        f"*To complete registration:*\n"
                        f"1. Click the registration button in the group\n"
                        f"2. Read and accept the declaration in DM\n\n"
                        f"*Note:* You will remain muted until you register."
                    )
                    reminder_sent = True
            
            # Send reminder if needed
            if reminder_sent:
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=reminder_text,
                        parse_mode="Markdown"
                    )
                    print(f"⏰ Sent reminder to user {user_id} after {hours} hours")
                except Exception as e:
                    print(f"⚠️ Could not send reminder to user {user_id}: {e}")
                    
    except Exception as e:
        print(f"Error in check_muted_users: {e}")


def setup_registration_handlers(application):
    """Setup all registration handlers"""
    
    # Handle private start command for registration
    application.add_handler(CommandHandler(
        "start", 
        handle_private_start,
        filters=filters.ChatType.PRIVATE
    ))
    
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
    
    # Callback for viewing rules in group
    application.add_handler(CallbackQueryHandler(
        view_rules_callback,
        pattern="^view_rules_"
    ))
    
    # Callback for accepting declaration in DM
    application.add_handler(CallbackQueryHandler(
        handle_accept_declaration,
        pattern="^accept_declaration_"
    ))
    
    # Callback for declining declaration in DM
    application.add_handler(CallbackQueryHandler(
        handle_decline_declaration,
        pattern="^decline_declaration_"
    ))
    
    print("✅ Registration handlers setup complete")