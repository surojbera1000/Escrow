"""Central configuration loaded from environment variables.

All runtime configuration is read from a ``.env`` file (see ``.env.example``).
Importing this module gives access to a single ``settings`` object.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name, default)
    if value is not None:
        value = value.strip()
    return value


def _get_int(name: str, default: int) -> int:
    raw = _get(name)
    try:
        return int(raw) if raw not in (None, "") else default
    except (TypeError, ValueError):
        return default


def _get_float(name: str, default: float) -> float:
    raw = _get(name)
    try:
        return float(raw) if raw not in (None, "") else default
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    # Telegram bot
    bot_token: str = field(default_factory=lambda: _get("BOT_TOKEN", "") or "")
    bot_username: str = field(default_factory=lambda: _get("BOT_USERNAME", "") or "")

    # Telethon user session (for group creation)
    api_id: int = field(default_factory=lambda: _get_int("API_ID", 0))
    api_hash: str = field(default_factory=lambda: _get("API_HASH", "") or "")
    userbot_phone: str = field(default_factory=lambda: _get("USERBOT_PHONE", "") or "")
    userbot_session: str = field(default_factory=lambda: _get("USERBOT_SESSION", "") or "")

    # MongoDB
    mongo_uri: str = field(default_factory=lambda: _get("MONGO_URI", "mongodb://localhost:27017") or "")
    mongo_db_name: str = field(default_factory=lambda: _get("MONGO_DB_NAME", "escrow_bot") or "")

    # Escrow behaviour
    escrow_fee_percent: float = field(default_factory=lambda: _get_float("ESCROW_FEE_PERCENT", 2.0))
    deposit_ttl_minutes: float = field(default_factory=lambda: _get_float("DEPOSIT_ADDRESS_TTL_MINUTES", 20.0))
    poll_interval_seconds: int = field(default_factory=lambda: _get_int("PAYMENT_POLL_INTERVAL_SECONDS", 60))
    group_photo_path: str = field(default_factory=lambda: _get("GROUP_PHOTO_PATH", "assets/escrow_group.jpg") or "")

    # Blockchain (only USDT on BSC / BEP20 is active in this build)
    bsc_rpc_url: str = field(default_factory=lambda: _get("BSC_RPC_URL", "https://bsc-dataseed.binance.org") or "")
    usdt_bep20_contract: str = field(
        default_factory=lambda: _get("USDT_BEP20_CONTRACT", "0x55d398326f99059fF775485246999027B3197955") or ""
    )
    # Single fixed escrow receiving address for USDT BEP20 deposits.
    bep20_deposit_address: str = field(
        default_factory=lambda: _get("BEP20_DEPOSIT_ADDRESS", "0xf5CDdbB7d687289aDfF413A48C7f1881910e6925") or ""
    )

    def validate(self) -> None:
        """Raise a clear error if mandatory settings are missing."""
        missing = []
        if not self.bot_token:
            missing.append("BOT_TOKEN")
        if not self.mongo_uri:
            missing.append("MONGO_URI")
        if missing:
            raise RuntimeError(
                "Missing required environment variables: " + ", ".join(missing) +
                ". Copy .env.example to .env and fill in the values."
            )


settings = Settings()
