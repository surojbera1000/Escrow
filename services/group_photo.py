"""
Group photo automation service.
Automatically changes the escrow group profile photo when a trade starts.
"""

import os
import logging
from telegram.ext import ContextTypes

from config.settings import GROUP_PHOTO_PATH

logger = logging.getLogger(__name__)


async def set_trade_active_photo(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> bool:
    """
    Change group photo to indicate an active trade.
    
    Args:
        context: Bot context
        chat_id: Group chat ID
        
    Returns:
        True if photo was changed successfully, False otherwise.
    """
    if not os.path.exists(GROUP_PHOTO_PATH):
        logger.warning(f"Group photo not found at: {GROUP_PHOTO_PATH}")
        return False

    try:
        with open(GROUP_PHOTO_PATH, "rb") as photo_file:
            await context.bot.set_chat_photo(
                chat_id=chat_id,
                photo=photo_file,
            )
        logger.info(f"Group photo updated for chat {chat_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to set group photo for chat {chat_id}: {e}")
        return False


async def remove_group_photo(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> bool:
    """
    Remove group photo (e.g., when trade is completed).
    
    Args:
        context: Bot context
        chat_id: Group chat ID
        
    Returns:
        True if photo was removed successfully, False otherwise.
    """
    try:
        await context.bot.delete_chat_photo(chat_id=chat_id)
        logger.info(f"Group photo removed for chat {chat_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to remove group photo for chat {chat_id}: {e}")
        return False
