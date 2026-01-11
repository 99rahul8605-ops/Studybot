#!/usr/bin/env python3
"""
Telegram Target Tracker Bot - Main Entry Point
"""
import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.bot_main import main

if __name__ == "__main__":
    main()
