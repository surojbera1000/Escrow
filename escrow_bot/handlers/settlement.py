"""/release, /refund (seller-only) and /dispute."""

from __future__ import annotations

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ..database import db
from ..models import TradeStatus
from ..utils import esc, is_group_chat, role_for_user


async def _require_seller(update: Update):
    """Return the trade if the caller is the assigned seller, else None (and reply)."""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if not is_group_chat(chat):
        await message.reply_text("This command can only be used inside the escrow group.")
        return None

    trade = await db.get_trade(chat.id)
    if not trade:
        await message.reply_text("No active trade in this group.")
        return None

    if role_for_user(trade, user.id) != "seller":
        await message.reply_text(
            "\u26d4 <b>Permission denied.</b> Only the assigned <b>seller</b> can use this command.",
            parse_mode=ParseMode.HTML,
        )
        return None

    return trade


async def release_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    trade = await _require_seller(update)
    if trade is None:
        return

    if trade.get("status") in (TradeStatus.RELEASED.value, TradeStatus.REFUNDED.value):
        await update.effective_message.reply_text("This trade is already settled.")
        return

    await db.set_status(update.effective_chat.id, TradeStatus.RELEASED.value)

    buyer = trade.get("buyer", {})
    await update.effective_message.reply_text(
        "\u2705 <b>Funds Released To Buyer.</b>\n\n"
        f"\U0001f4b3 Payout wallet: <code>{esc(buyer.get('wallet', '-'))}</code>\n"
        "Thank you for using our escrow service!",
        parse_mode=ParseMode.HTML,
    )


async def refund_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    trade = await _require_seller(update)
    if trade is None:
        return

    if trade.get("status") in (TradeStatus.RELEASED.value, TradeStatus.REFUNDED.value):
        await update.effective_message.reply_text("This trade is already settled.")
        return

    await db.set_status(update.effective_chat.id, TradeStatus.REFUNDED.value)

    seller = trade.get("seller", {})
    await update.effective_message.reply_text(
        "\u21a9\ufe0f <b>Funds Refunded To Seller.</b>\n\n"
        f"\U0001f4b3 Payout wallet: <code>{esc(seller.get('wallet', '-'))}</code>",
        parse_mode=ParseMode.HTML,
    )


async def dispute_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if not is_group_chat(chat):
        await message.reply_text("Use /dispute inside the escrow group.")
        return

    trade = await db.get_trade(chat.id)
    if not trade:
        await message.reply_text("No active trade in this group.")
        return

    if role_for_user(trade, user.id) is None:
        await message.reply_text("Only the buyer or seller can raise a dispute.")
        return

    await db.set_status(chat.id, TradeStatus.DISPUTED.value)
    await message.reply_text(
        "\u26a0\ufe0f <b>Dispute Raised.</b>\n\n"
        "Funds are now <b>frozen</b> until a moderator reviews this trade. "
        "Both parties, please share your evidence here. A moderator will join shortly.",
        parse_mode=ParseMode.HTML,
    )
