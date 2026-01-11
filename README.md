# Telegram Target Tracker Bot - Registration Flow

## Complete Registration Process:

### Step-by-Step Flow:
1. **New Member Joins Group**
   - Bot automatically detects new member
   - Mutes the member (if bot is admin)
   - Sends welcome message with registration button

2. **Registration Button**
   - Button: "Complete Registration (DM Bot)"
   - Opens private chat with bot
   - URL format: `https://t.me/YourBotUsername?start=register_GROUP_ID`

3. **Declaration in DM**
   - Bot shows group rules declaration
   - Two inline buttons: "I ACCEPT" or "I DECLINE"
   - User must click "I ACCEPT" to continue

4. **Registration Complete**
   - Bot verifies registration in database
   - Automatically unmutes user in group
   - Sends success message in DM
   - Announces in group that user is now verified

5. **User Can Now Participate**
   - Can send messages in group
   - Can use all bot commands
   - Can set targets and share sentences

## Bot Admin Requirements:

For registration to work, the bot **MUST** be an admin in the group with these permissions:

### Required Admin Permissions:
- ✅ **Delete messages** - To delete messages from unregistered users
- ✅ **Restrict members** - To mute/unmute users
- ✅ **Ban members** - For future features

### How to Make Bot Admin:
1. Go to group settings
2. Add bot as administrator
3. Enable all required permissions
4. Save changes

## Testing the Registration:

### Test with Two Accounts:
1. **Account A** - Bot admin (already in group)
2. **Account B** - New member (test account)

### Test Steps:
1. Add Account B to the group
2. Bot should automatically mute Account B
3. Bot should send welcome message with registration button
4. Click button with Account B (opens DM)
5. Accept declaration in DM
6. Account B should be automatically unmuted in group
7. Account B can now send messages and use bot commands

## Troubleshooting:

### Issue: Bot not muting new members
**Solution:**
- Check if bot is admin
- Check admin permissions
- Restart bot after making bot admin

### Issue: Registration button not working
**Solution:**
- Check bot username is correct
- Ensure bot is started (use `/start` command in group first)
- Check MongoDB connection

### Issue: User not getting unmuted after registration
**Solution:**
- Bot needs "Restrict members" permission
- Check if user clicked "I ACCEPT" in DM
- Check MongoDB for registration status

## Commands for Testing:

### Reset All Data (Admin):
