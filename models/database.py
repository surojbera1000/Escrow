"""
MongoDB connection and database initialization.
"""

from pymongo import MongoClient
from pymongo.database import Database
from config.settings import MONGODB_URI, MONGODB_DB_NAME


class MongoDB:
    """Singleton MongoDB connection manager."""

    _client: MongoClient = None
    _db: Database = None

    @classmethod
    def connect(cls) -> Database:
        """Establish connection to MongoDB and return database instance."""
        if cls._client is None:
            cls._client = MongoClient(MONGODB_URI)
            cls._db = cls._client[MONGODB_DB_NAME]
            cls._create_indexes()
        return cls._db

    @classmethod
    def get_db(cls) -> Database:
        """Get database instance, connecting if necessary."""
        if cls._db is None:
            return cls.connect()
        return cls._db

    @classmethod
    def _create_indexes(cls):
        """Create database indexes for performance."""
        # Trades collection indexes
        cls._db.trades.create_index("group_id", unique=True)
        cls._db.trades.create_index("status")
        cls._db.trades.create_index("created_at")

        # Users collection indexes
        cls._db.users.create_index("user_id", unique=True)

        # Escrow groups collection indexes
        cls._db.escrow_groups.create_index("group_id", unique=True)
        cls._db.escrow_groups.create_index("creator_id")

        # Wallets collection indexes
        cls._db.wallets.create_index("trade_id")
        cls._db.wallets.create_index("address")

    @classmethod
    def close(cls):
        """Close MongoDB connection."""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
