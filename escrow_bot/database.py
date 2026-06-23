"""Async MongoDB access layer.

Collections
-----------
- ``trades``  : one document per escrow deal (keyed by the group chat id)
- ``users``   : optional cache of users that interacted with the bot
- ``sessions``: Telethon session metadata (not used for the StringSession flow)

A trade document looks like::

    {
        "chat_id": -1001234567890,        # escrow group id
        "creator_id": 111,                 # user who ran /escrow
        "invite_link": "https://t.me/...",
        "status": "open",                  # open|accepted|deposited|paid|released|refunded|disputed
        "deal": {"quantity": "...", "rate": "...", "conditions": "..."},
        "seller": {"user_id": 1, "username": "...", "wallet": "..."},
        "buyer":  {"user_id": 2, "username": "...", "wallet": "..."},
        "token": "USDT",
        "network": "BEP20",
        "deposit": {
            "address": "0x...",
            "private_key": "...",          # encrypted/stored for sweep (handle with care!)
            "expires_at": <datetime>,
            "amount_expected": 100.0,
            "amount_received": 0.0,
        },
        "created_at": <datetime>,
        "updated_at": <datetime>,
    }
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from .config import settings


class Database:
    """Thin async wrapper around the trade/user collections."""

    def __init__(self, uri: str | None = None, db_name: str | None = None) -> None:
        self._client: Optional[AsyncIOMotorClient] = None
        self._uri = uri or settings.mongo_uri
        self._db_name = db_name or settings.mongo_db_name
        self._db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        self._client = AsyncIOMotorClient(self._uri)
        self._db = self._client[self._db_name]
        # Helpful indexes
        await self._db.trades.create_index("chat_id", unique=True)
        await self._db.trades.create_index("deposit.address")
        await self._db.users.create_index("user_id", unique=True)

    async def close(self) -> None:
        if self._client is not None:
            self._client.close()

    @property
    def db(self) -> AsyncIOMotorDatabase:
        if self._db is None:
            raise RuntimeError("Database.connect() must be called before use.")
        return self._db

    # ------------------------------------------------------------------ trades
    async def create_trade(self, chat_id: int, creator_id: int, invite_link: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        doc = {
            "chat_id": chat_id,
            "creator_id": creator_id,
            "invite_link": invite_link,
            "status": "open",
            "deal": {},
            "seller": {},
            "buyer": {},
            "token": None,
            "network": None,
            "deposit": {},
            "created_at": now,
            "updated_at": now,
        }
        await self.db.trades.update_one(
            {"chat_id": chat_id}, {"$setOnInsert": doc}, upsert=True
        )
        return await self.get_trade(chat_id)  # type: ignore[return-value]

    async def get_trade(self, chat_id: int) -> Optional[Dict[str, Any]]:
        return await self.db.trades.find_one({"chat_id": chat_id})

    async def get_trade_by_address(self, address: str) -> Optional[Dict[str, Any]]:
        return await self.db.trades.find_one({"deposit.address": address})

    async def update_trade(self, chat_id: int, updates: Dict[str, Any]) -> None:
        updates = dict(updates)
        updates["updated_at"] = datetime.now(timezone.utc)
        await self.db.trades.update_one({"chat_id": chat_id}, {"$set": updates})

    async def set_status(self, chat_id: int, status: str) -> None:
        await self.update_trade(chat_id, {"status": status})

    async def set_role(self, chat_id: int, role: str, data: Dict[str, Any]) -> None:
        """role is 'seller' or 'buyer'."""
        assert role in ("seller", "buyer")
        await self.update_trade(chat_id, {role: data})

    async def iter_active_deposits(self):
        """Yield trades that currently have a deposit address awaiting payment."""
        cursor = self.db.trades.find(
            {"status": {"$in": ["deposited"]}, "deposit.address": {"$exists": True}}
        )
        async for doc in cursor:
            yield doc

    # ------------------------------------------------------------------- users
    async def upsert_user(self, user_id: int, username: Optional[str], first_name: Optional[str]) -> None:
        await self.db.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "username": username,
                    "first_name": first_name,
                    "last_seen": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )


# Shared singleton used across handlers
db = Database()
