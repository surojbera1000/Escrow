"""
User model for managing users in MongoDB.
"""

from datetime import datetime
from typing import Optional
from models.database import MongoDB


class UserModel:
    """User database operations."""

    @staticmethod
    def create_or_update_user(user_id: int, username: str, first_name: str = "", last_name: str = "") -> dict:
        """Create or update a user record."""
        db = MongoDB.get_db()
        user = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "total_trades": 0,
            "successful_trades": 0,
            "updated_at": datetime.utcnow(),
        }
        db.users.update_one(
            {"user_id": user_id},
            {"$set": user, "$setOnInsert": {"created_at": datetime.utcnow()}},
            upsert=True,
        )
        return user

    @staticmethod
    def get_user(user_id: int) -> Optional[dict]:
        """Get user by user ID."""
        db = MongoDB.get_db()
        return db.users.find_one({"user_id": user_id})

    @staticmethod
    def increment_trades(user_id: int, successful: bool = False):
        """Increment trade count for a user."""
        db = MongoDB.get_db()
        update = {"$inc": {"total_trades": 1}}
        if successful:
            update["$inc"]["successful_trades"] = 1
        db.users.update_one({"user_id": user_id}, update)
