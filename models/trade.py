"""
Trade model for managing escrow trades in MongoDB.
"""

from datetime import datetime
from typing import Optional
from models.database import MongoDB


class TradeStatus:
    """Trade status constants."""
    CREATED = "created"
    DEAL_SET = "deal_set"
    ROLES_ASSIGNED = "roles_assigned"
    TOKEN_SELECTED = "token_selected"
    ACCEPTED = "accepted"
    DEPOSIT_PENDING = "deposit_pending"
    DEPOSIT_RECEIVED = "deposit_received"
    RELEASED = "released"
    REFUNDED = "refunded"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class TradeModel:
    """Trade database operations."""

    @staticmethod
    def create_trade(group_id: int, creator_id: int, creator_username: str) -> dict:
        """Create a new trade record."""
        db = MongoDB.get_db()
        trade = {
            "group_id": group_id,
            "creator_id": creator_id,
            "creator_username": creator_username,
            "status": TradeStatus.CREATED,
            "seller": None,
            "buyer": None,
            "token": None,
            "network": None,
            "quantity": None,
            "rate": None,
            "conditions": None,
            "deposit_address": None,
            "deposit_amount": 0.0,
            "amount_received": 0.0,
            "start_time": None,
            "end_time": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        db.trades.insert_one(trade)
        return trade

    @staticmethod
    def get_trade_by_group(group_id: int) -> Optional[dict]:
        """Get trade by group ID."""
        db = MongoDB.get_db()
        return db.trades.find_one({"group_id": group_id})

    @staticmethod
    def set_deal_info(group_id: int, quantity: str, rate: str, conditions: str) -> bool:
        """Set deal info for a trade."""
        db = MongoDB.get_db()
        result = db.trades.update_one(
            {"group_id": group_id},
            {
                "$set": {
                    "quantity": quantity,
                    "rate": rate,
                    "conditions": conditions,
                    "status": TradeStatus.DEAL_SET,
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0

    @staticmethod
    def set_seller(group_id: int, user_id: int, username: str, wallet_address: str) -> bool:
        """Set seller for a trade."""
        db = MongoDB.get_db()
        result = db.trades.update_one(
            {"group_id": group_id},
            {
                "$set": {
                    "seller": {
                        "user_id": user_id,
                        "username": username,
                        "wallet_address": wallet_address,
                    },
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0

    @staticmethod
    def set_buyer(group_id: int, user_id: int, username: str, wallet_address: str) -> bool:
        """Set buyer for a trade."""
        db = MongoDB.get_db()
        result = db.trades.update_one(
            {"group_id": group_id},
            {
                "$set": {
                    "buyer": {
                        "user_id": user_id,
                        "username": username,
                        "wallet_address": wallet_address,
                    },
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0

    @staticmethod
    def set_token_network(group_id: int, token: str, network: str) -> bool:
        """Set token and network for a trade."""
        db = MongoDB.get_db()
        result = db.trades.update_one(
            {"group_id": group_id},
            {
                "$set": {
                    "token": token,
                    "network": network,
                    "status": TradeStatus.TOKEN_SELECTED,
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0

    @staticmethod
    def accept_trade(group_id: int) -> bool:
        """Accept a trade - mark as accepted and record start time."""
        db = MongoDB.get_db()
        result = db.trades.update_one(
            {"group_id": group_id},
            {
                "$set": {
                    "status": TradeStatus.ACCEPTED,
                    "start_time": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0

    @staticmethod
    def set_deposit_address(group_id: int, address: str) -> bool:
        """Set deposit address for a trade."""
        db = MongoDB.get_db()
        result = db.trades.update_one(
            {"group_id": group_id},
            {
                "$set": {
                    "deposit_address": address,
                    "status": TradeStatus.DEPOSIT_PENDING,
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0

    @staticmethod
    def update_amount_received(group_id: int, amount: float) -> bool:
        """Update amount received for a trade."""
        db = MongoDB.get_db()
        result = db.trades.update_one(
            {"group_id": group_id},
            {
                "$set": {
                    "amount_received": amount,
                    "status": TradeStatus.DEPOSIT_RECEIVED,
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0

    @staticmethod
    def release_funds(group_id: int) -> bool:
        """Mark trade funds as released."""
        db = MongoDB.get_db()
        result = db.trades.update_one(
            {"group_id": group_id},
            {
                "$set": {
                    "status": TradeStatus.RELEASED,
                    "end_time": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0

    @staticmethod
    def refund_funds(group_id: int) -> bool:
        """Mark trade funds as refunded."""
        db = MongoDB.get_db()
        result = db.trades.update_one(
            {"group_id": group_id},
            {
                "$set": {
                    "status": TradeStatus.REFUNDED,
                    "end_time": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0

    @staticmethod
    def set_dispute(group_id: int) -> bool:
        """Mark trade as disputed."""
        db = MongoDB.get_db()
        result = db.trades.update_one(
            {"group_id": group_id},
            {
                "$set": {
                    "status": TradeStatus.DISPUTED,
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0
