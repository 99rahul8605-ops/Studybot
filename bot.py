#!/usr/bin/env python3
"""
Telegram Target Tracker Bot - Main Entry Point
"""
import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Simple health check - just check environment variables
print("🤖 Starting Target Tracker Bot - Health Check...")
print("=" * 50)

# Check required environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")

if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN environment variable is required!")
    print("Please set BOT_TOKEN in your environment variables")
    sys.exit(1)

print(f"✅ BOT_TOKEN: Set")
print(f"✅ MONGODB_URI: {'Set' if MONGODB_URI else 'Not set (using default)'}")

print("=" * 50)
print("✅ All checks passed. Starting bot...")

from src.bot_main import main

if __name__ == "__main__":
    main()
