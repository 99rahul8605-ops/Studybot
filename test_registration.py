"""
Test script to verify registration flow
"""
import asyncio
from telegram import Bot
import os
from dotenv import load_dotenv

load_dotenv()

async def test_bot_info():
    """Test bot information"""
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not found")
        return
    
    bot = Bot(token=BOT_TOKEN)
    
    try:
        # Get bot info
        me = await bot.get_me()
        print(f"✅ Bot Info:")
        print(f"   Username: @{me.username}")
        print(f"   Name: {me.first_name}")
        print(f"   ID: {me.id}")
        
        # Test registration URL
        group_id = -1001234567890  # Example group ID
        registration_url = f"https://t.me/{me.username}?start=register_{group_id}"
        print(f"\n✅ Registration URL Format:")
        print(f"   {registration_url}")
        
        # Test if bot can get updates
        updates = await bot.get_updates(limit=1)
        if updates:
            print(f"\n✅ Bot has updates")
        else:
            print(f"\n⚠️ Bot has no updates yet")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await bot.close()

if __name__ == '__main__':
    asyncio.run(test_bot_info())
