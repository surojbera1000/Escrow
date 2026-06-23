"""/escrow - create a new private escrow group and return the invite link."""

from __future__ import annotations

import logging
import secrets

from telegram import Update
from telegram.constants import ChatType, ParseMode
from telegram.ext import ContextTypes

from ..database import db
from ..services.group_manager import group_manager

logger = logging.getLogger(__name__)

PINNED_WELCOME = (
    "Hey there traders! \U0001f44b\n\n"
    "Welcome to our escrow service. Please start with the /dd command and "
    "fill the DealInfo Form."
)


async def escrow_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Triggered in the bot's private chat. Creates a fresh escrow group."""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if chat.type != ChatType.PRIVATE:
        await message.reply_text(
            "Please use /escrow in a private chat with me to create a new escrow group."
        )
        return

    deal_ref = secrets.token_hex(3).upper()

    if not group_manager.available:
        # Graceful fallback when no userbot session is configured.
        await message.reply_text(
            "\u26a0\ufe0f Automatic group creation isn't configured on this instance.\n\n"
            "To finish setup, the operator must add a Telethon user session "
            "(API_ID / API_HASH / USERBOT_SESSION).\n\n"
            "<b>Manual alternative:</b>\n"
            "1. Create a private group yourself.\n"
            f"2. Add me (@{context.bot.username}) and make me an <b>administrator</b>.\n"
            "3. Run /dd inside the group to begin the deal.",
            parse_mode=ParseMode.HTML,
        )
        return

    await message.reply_text("\u23f3 Creating your private escrow group...")

    try:
        created = await group_manager.create_escrow_group(deal_ref)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Group creation failed")
        await message.reply_text(
            "\u274c Sorry, I couldn't create the group right now. Please try again later."
        )
        return

    if created is None:
        await message.reply_text(
            "\u274c Group creation is unavailable. Please contact support."
        )
        return

    # Record the trade keyed by the new group's chat id.
    await db.create_trade(
        chat_id=created.chat_id, creator_id=user.id, invite_link=created.invite_link
    )

    # Post + pin the welcome message inside the new group.
    try:
        sent = await context.bot.send_message(
            chat_id=created.chat_id, text=PINNED_WELCOME
        )
        await context.bot.pin_chat_message(
            chat_id=created.chat_id, message_id=sent.message_id, disable_notification=True
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not post/pin welcome message: %s", exc)

    # Send the invite link back to the user's private chat.
    await message.reply_text(
        "\u2705 <b>Your escrow group is ready!</b>\n\n"
        f"\U0001f517 <a href=\"{created.invite_link}\">{created.invite_link}</a>\n\n"
        "Join this escrow group and share the link with the buyer and seller.",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
