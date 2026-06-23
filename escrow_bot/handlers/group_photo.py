"""Automatic group profile photo change once a trade starts."""

from __future__ import annotations

import logging
import os

from telegram.ext import ContextTypes

from ..config import settings

logger = logging.getLogger(__name__)


async def set_trade_group_photo(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> bool:
    """Set the escrow group's profile photo from ``GROUP_PHOTO_PATH``.

    Requires the bot to be an admin with ``can_change_info``. Returns True on
    success, False otherwise (missing file / permissions). Failures are logged
    but never raised, so they can't break the trade flow.
    """
    photo_path = settings.group_photo_path
    if not photo_path or not os.path.isfile(photo_path):
        logger.info("Group photo not set: file '%s' not found.", photo_path)
        return False

    try:
        with open(photo_path, "rb") as fh:
            await context.bot.set_chat_photo(chat_id=chat_id, photo=fh)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not change group photo for %s: %s", chat_id, exc)
        return False
