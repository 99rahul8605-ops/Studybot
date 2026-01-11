import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

load_dotenv()

class MongoDB:
    def __init__(self):
        self.mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        self.db_name = os.getenv("DB_NAME", "telegram_target_bot")
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self._create_collections()
            print("✅ Connected to MongoDB successfully!")
        except ConnectionFailure as e:
            print(f"❌ MongoDB connection failed: {e}")
    
    def _create_collections(self):
        # Create collections if they don't exist
        collections = self.db.list_collection_names()
        
        if "users" not in collections:
            self.db.create_collection("users")
            self.db.users.create_index("user_id", unique=True)
        
        if "targets" not in collections:
            self.db.create_collection("targets")
            self.db.targets.create_index([("user_id", 1), ("date", 1)], unique=True)
            self.db.targets.create_index([("group_id", 1), ("date", 1)])
        
        if "group_settings" not in collections:
            self.db.create_collection("group_settings")
            self.db.group_settings.create_index("group_id", unique=True)
        
        if "registrations" not in collections:
            self.db.create_collection("registrations")
            self.db.registrations.create_index([("user_id", 1), ("group_id", 1)], unique=True)
            self.db.registrations.create_index("verification_code")
        
        if "muted_users" not in collections:
            self.db.create_collection("muted_users")
            self.db.muted_users.create_index([("user_id", 1), ("group_id", 1)], unique=True)
            self.db.muted_users.create_index("muted_until", expireAfterSeconds=0)
    
    def add_target(self, group_id: int, user_id: int, username: str, target: str, date: datetime = None):
        """Add a target for a user on a specific date"""
        if date is None:
            date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        target_data = {
            "group_id": group_id,
            "user_id": user_id,
            "username": username,
            "target": target,
            "date": date,
            "created_at": datetime.now(),
            "completed": False
        }
        
        try:
            self.db.targets.update_one(
                {"user_id": user_id, "date": date},
                {"$set": target_data},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error adding target: {e}")
            return False
    
    def get_today_target(self, user_id: int):
        """Get today's target for a user"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return self.db.targets.find_one({"user_id": user_id, "date": today})
    
    def get_all_targets(self, group_id: int, date: datetime = None):
        """Get all targets for a group on a specific date"""
        if date is None:
            date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        return list(self.db.targets.find({
            "group_id": group_id,
            "date": date
        }))
    
    def get_user_targets(self, user_id: int, limit: int = 7):
        """Get recent targets for a user"""
        return list(self.db.targets.find(
            {"user_id": user_id}
        ).sort("date", -1).limit(limit))
    
    def mark_target_completed(self, user_id: int, date: datetime = None):
        """Mark a target as completed"""
        if date is None:
            date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        return self.db.targets.update_one(
            {"user_id": user_id, "date": date},
            {"$set": {"completed": True, "completed_at": datetime.now()}}
        )
    
    def reset_all_data(self, group_id: int = None):
        """Reset all data (for testing)"""
        try:
            if group_id:
                self.db.targets.delete_many({"group_id": group_id})
                self.db.group_settings.delete_one({"group_id": group_id})
                self.db.registrations.delete_many({"group_id": group_id})
                self.db.muted_users.delete_many({"group_id": group_id})
            else:
                self.db.targets.delete_many({})
                self.db.group_settings.delete_many({})
                self.db.registrations.delete_many({})
                self.db.muted_users.delete_many({})
            return True
        except Exception as e:
            print(f"Error resetting data: {e}")
            return False
    
    def set_allowed_group(self, group_id: int, group_name: str):
        """Set the allowed group for the bot"""
        self.db.group_settings.update_one(
            {"group_id": group_id},
            {"$set": {
                "group_id": group_id,
                "group_name": group_name,
                "updated_at": datetime.now()
            }},
            upsert=True
        )
    
    def is_group_allowed(self, group_id: int) -> bool:
        """Check if a group is allowed"""
        # If no groups are set, allow all (for initial setup)
        count = self.db.group_settings.count_documents({})
        if count == 0:
            return True
        
        return self.db.group_settings.find_one({"group_id": group_id}) is not None
    
    def get_allowed_group(self):
        """Get the allowed group info"""
        return self.db.group_settings.find_one()
    
    # New Registration Functions
    
    def create_registration(self, user_id: int, group_id: int, username: str = None):
        """Create a new registration record for user"""
        import secrets
        verification_code = secrets.token_hex(3).upper()  # 6-character code
        
        registration_data = {
            "user_id": user_id,
            "group_id": group_id,
            "username": username,
            "verification_code": verification_code,
            "status": "pending",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        try:
            self.db.registrations.update_one(
                {"user_id": user_id, "group_id": group_id},
                {"$set": registration_data},
                upsert=True
            )
            return verification_code
        except Exception as e:
            print(f"Error creating registration: {e}")
            return None
    
    def get_registration(self, user_id: int, group_id: int):
        """Get registration data for user"""
        return self.db.registrations.find_one({"user_id": user_id, "group_id": group_id})
    
    def verify_registration(self, user_id: int, group_id: int, code: str) -> bool:
        """Verify registration code"""
        registration = self.db.registrations.find_one({
            "user_id": user_id,
            "group_id": group_id,
            "verification_code": code,
            "status": "pending"
        })
        
        if registration:
            self.db.registrations.update_one(
                {"user_id": user_id, "group_id": group_id},
                {"$set": {
                    "status": "verified",
                    "verified_at": datetime.now(),
                    "updated_at": datetime.now()
                }}
            )
            
            # Remove from muted users
            self.db.muted_users.delete_one({"user_id": user_id, "group_id": group_id})
            
            return True
        return False
    
    def is_user_verified(self, user_id: int, group_id: int) -> bool:
        """Check if user is verified in group"""
        registration = self.db.registrations.find_one({
            "user_id": user_id,
            "group_id": group_id,
            "status": "verified"
        })
        return registration is not None
    
    # Mute Functions
    
    def mute_user(self, user_id: int, group_id: int, hours: int = 24):
        """Mute user for specified hours"""
        muted_until = datetime.now() + timedelta(hours=hours)
        
        mute_data = {
            "user_id": user_id,
            "group_id": group_id,
            "muted_at": datetime.now(),
            "muted_until": muted_until,
            "reason": "pending_registration"
        }
        
        try:
            self.db.muted_users.update_one(
                {"user_id": user_id, "group_id": group_id},
                {"$set": mute_data},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error muting user: {e}")
            return False
    
    def is_user_muted(self, user_id: int, group_id: int) -> bool:
        """Check if user is currently muted"""
        mute_record = self.db.muted_users.find_one({
            "user_id": user_id,
            "group_id": group_id,
            "muted_until": {"$gt": datetime.now()}
        })
        return mute_record is not None
    
    def unmute_user(self, user_id: int, group_id: int):
        """Unmute user"""
        result = self.db.muted_users.delete_one({"user_id": user_id, "group_id": group_id})
        return result.deleted_count > 0
    
    def get_muted_users(self, group_id: int):
        """Get all muted users in group"""
        return list(self.db.muted_users.find({
            "group_id": group_id,
            "muted_until": {"$gt": datetime.now()}
        }))
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()

# Global database instance
db = MongoDB()
