"""Small helpers shared across handlers."""

from __future__ import annotations

import html
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from telegram import Chat, User


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def fmt_time(dt: Optional[datetime]) -> str:
    if dt is None:
        return "-"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def esc(text: Any) -> str:
    """HTML-escape a value for safe use in Telegram HTML messages."""
    return html.escape(str(text)) if text is not None else "-"


def user_mention(user: User) -> str:
    """Return an HTML mention link for a user."""
    name = esc(user.full_name or user.username or str(user.id))
    return f'<a href="tg://user?id={user.id}">{name}</a>'


def display_username(username: Optional[str], user_id: Optional[int]) -> str:
    if username:
        return f"@{username}"
    return f"id:{user_id}" if user_id else "-"


def is_group_chat(chat: Chat) -> bool:
    return chat.type in (Chat.GROUP, Chat.SUPERGROUP)


def short_addr(address: Optional[str], head: int = 8, tail: int = 6) -> str:
    if not address:
        return "-"
    if len(address) <= head + tail + 3:
        return address
    return f"{address[:head]}...{address[-tail:]}"


def role_for_user(trade: Dict[str, Any], user_id: int) -> Optional[str]:
    """Return 'seller'/'buyer' if the given user holds that role in the trade."""
    if trade.get("seller", {}).get("user_id") == user_id:
        return "seller"
    if trade.get("buyer", {}).get("user_id") == user_id:
        return "buyer"
    return None
