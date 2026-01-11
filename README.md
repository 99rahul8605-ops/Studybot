# Telegram Member Target Bot

A Telegram bot that works only in a specified group and allows adding targets for members.

## Features

- ✅ Works only in a specified group (security)
- ✅ Add member targets using commands
- ✅ View individual member targets
- ✅ List all member targets
- ✅ Remove member targets
- ✅ Docker support for easy deployment
- ✅ Ready for Render free plan

## Setup Instructions

### 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Get Your Group ID

1. Add your bot to the group where you want it to work
2. Send a message in the group
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Look for `"chat":{"id":-1001234567890` - this number is your group ID
5. Remove the bot from the group (you'll add it back later)

### 3. Deploy to Render

#### Option A: Deploy via GitHub (Recommended)

1. Create a GitHub repository and push all these files
2. Go to [Render](https://render.com) and sign up/login
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Name**: telegram-member-bot (or any name)
   - **Environment**: Docker
   - **Region**: Choose closest to you
   - **Branch**: main
   - **Instance Type**: Free
6. Add Environment Variables:
   - `BOT_TOKEN`: Your bot token from BotFather
   - `ALLOWED_GROUP_ID`: Your group ID (with the minus sign)
7. Click "Create Web Service"

#### Option B: Local Testing

1. Clone the repository
2. Create `.env` file:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add your bot token and group ID
4. Run with Docker:
   ```bash
   docker build -t telegram-bot .
   docker run --env-file .env telegram-bot
   ```

### 4. Add Bot to Your Group

1. Add your bot back to the group
2. Make sure to give it admin rights (or at least permission to read messages)
3. Send `/start` in the group to test

## Bot Commands

- `/start` - Start the bot and see welcome message
- `/addtarget <username> <target>` - Add a target for a member
  - Example: `/addtarget @john 50 messages per day`
- `/viewtarget <username>` - View target for a specific member
  - Example: `/viewtarget @john`
- `/listtargets` - List all member targets
- `/removetarget <username>` - Remove a member's target
  - Example: `/removetarget @john`
- `/help` - Show help message

## Important Notes

### For Render Free Plan:

- The free plan may sleep after 15 minutes of inactivity
- The bot will wake up when a request comes in (may take 30-60 seconds)
- You get 750 hours/month of runtime (enough for 24/7 if you only have one service)
- Consider upgrading to a paid plan for production use

### Security:

- The bot only responds to commands in the specified group
- Store your bot token and group ID as environment variables (never commit them)
- Keep your `.env` file in `.gitignore`

## File Structure

```
telegram-member-bot/
├── bot.py              # Main bot code
├── requirements.txt    # Python dependencies
├── Dockerfile         # Docker configuration
├── .dockerignore      # Files to ignore in Docker
├── .gitignore         # Files to ignore in Git
├── .env.example       # Example environment variables
└── README.md          # This file
```

## Troubleshooting

### Bot doesn't respond:
1. Check if bot token is correct in environment variables
2. Verify group ID is correct (including minus sign)
3. Ensure bot has permission to read messages in the group
4. Check Render logs for errors

### Get Group ID:
If you're having trouble getting the group ID:
1. Add the bot to your group
2. Send any message in the group
3. Open: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
4. Find the "chat" object with "type": "group" or "supergroup"
5. The "id" field is your group ID

### Render Deployment Issues:
- Make sure you selected "Docker" as the environment
- Verify environment variables are set correctly in Render dashboard
- Check the deployment logs in Render for any errors

## Upgrading

To add persistence (database) or more features, you can:
- Add PostgreSQL database (Render offers free PostgreSQL)
- Implement user authentication
- Add more complex target tracking
- Set up notifications and reminders

## License

This project is open source and available for personal and commercial use.
