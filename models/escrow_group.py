"""
Escrow Group model for managing escrow groups in MongoDB.
"""

from datetime import datetime
from typing import Optional
from models.database import MongoDB


class EscrowGroupModel:
    """Escrow group database operations."""

    @staticmethod
    def create_group(group_id: int, creator_id: int, invite_link: str, group_title: str) -> dict:
        """Create a new escrow group record."""
        db = MongoDB.get_db()
        group = {
            "group_id": group_id,
            "creator_id": creator_id,
            "invite_link": invite_link,
            "group_title": group_title,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        db.escrow_groups.insert_one(group)
        return group

    @staticmethod
    def get_group(group_id: int) -> Optional[dict]:
        """Get escrow group by group ID."""
        db = MongoDB.get_db()
        return db.escrow_groups.find_one({"group_id": group_id})

    @staticmethod
    def deactivate_group(group_id: int) -> bool:
        """Deactivate an escrow group."""
        db = MongoDB.get_db()
        result = db.escrow_groups.update_one(
            {"group_id": group_id},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}},
        )
        return result.modified_count > 0
