"""
Telegram Target Tracker Bot
A bot to track daily targets for group members.
"""
__version__ = "1.0.0"
__author__ = "Target Tracker Bot"

# Import key components for easier access
from src.database import db
from src.utils import is_admin, format_targets_message
