"""
Handlers for /release, /refund, and /dispute commands.
Strict permission checks: ONLY the assigned seller can release/refund.
"""

from telegram import Update
from telegram.ext import ContextTypes

from utils.messages import (
    funds_released_message,
    funds_refunded_message,
    dispute_opened_message,
)
from models.trade import TradeModel, TradeStatus


async def release_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /release command - release funds to buyer (seller only)."""
    chat = update.effective_chat
    user = update.effective_user

    # Only allow in groups
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text(
            "⚠️ This command can only be used in an escrow group.",
            parse_mode="HTML",
        )
        return

    # Get trade info
    trade = TradeModel.get_trade_by_group(chat.id)
    if not trade:
        await update.message.reply_text(
            "⚠️ No active trade in this group.",
            parse_mode="HTML",
        )
        return

    # PERMISSION CHECK: Only seller can release
    seller = trade.get("seller")
    if not seller:
        await update.message.reply_text(
            "⚠️ No seller assigned to this trade.",
            parse_mode="HTML",
        )
        return

    if seller["user_id"] != user.id:
        await update.message.reply_text(
            "🚫 <b>ACCESS DENIED</b>\n\n"
            "Only the assigned <b>Seller</b> can release funds.\n"
            f"Current Seller: @{seller['username']}",
            parse_mode="HTML",
        )
        return


    # Check trade status
    valid_statuses = (TradeStatus.DEPOSIT_RECEIVED, TradeStatus.DEPOSIT_PENDING, TradeStatus.ACCEPTED)
    if trade.get("status") not in valid_statuses:
        await update.message.reply_text(
            "⚠️ Cannot release funds. Trade status: "
            f"<code>{trade.get('status', 'unknown')}</code>",
            parse_mode="HTML",
        )
        return

    # Release funds
    TradeModel.release_funds(group_id=chat.id)

    buyer = trade.get("buyer", {})
    await update.message.reply_text(
        funds_released_message(buyer.get("username", "Unknown")),
        parse_mode="HTML",
    )


async def refund_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /refund command - refund funds to seller (seller only)."""
    chat = update.effective_chat
    user = update.effective_user

    # Only allow in groups
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text(
            "⚠️ This command can only be used in an escrow group.",
            parse_mode="HTML",
        )
        return

    # Get trade info
    trade = TradeModel.get_trade_by_group(chat.id)
    if not trade:
        await update.message.reply_text(
            "⚠️ No active trade in this group.",
            parse_mode="HTML",
        )
        return

    # PERMISSION CHECK: Only seller can refund
    seller = trade.get("seller")
    if not seller:
        await update.message.reply_text(
            "⚠️ No seller assigned to this trade.",
            parse_mode="HTML",
        )
        return

    if seller["user_id"] != user.id:
        await update.message.reply_text(
            "🚫 <b>ACCESS DENIED</b>\n\n"
            "Only the assigned <b>Seller</b> can refund funds.\n"
            f"Current Seller: @{seller['username']}",
            parse_mode="HTML",
        )
        return

    # Check trade status
    valid_statuses = (TradeStatus.DEPOSIT_RECEIVED, TradeStatus.DEPOSIT_PENDING, TradeStatus.ACCEPTED)
    if trade.get("status") not in valid_statuses:
        await update.message.reply_text(
            "⚠️ Cannot refund. Trade status: "
            f"<code>{trade.get('status', 'unknown')}</code>",
            parse_mode="HTML",
        )
        return

    # Refund funds
    TradeModel.refund_funds(group_id=chat.id)

    await update.message.reply_text(
        funds_refunded_message(seller.get("username", "Unknown")),
        parse_mode="HTML",
    )


async def dispute_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /dispute command - open a dispute."""
    chat = update.effective_chat
    user = update.effective_user

    # Only allow in groups
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text(
            "⚠️ This command can only be used in an escrow group.",
            parse_mode="HTML",
        )
        return

    # Get trade info
    trade = TradeModel.get_trade_by_group(chat.id)
    if not trade:
        await update.message.reply_text(
            "⚠️ No active trade in this group.",
            parse_mode="HTML",
        )
        return

    # Only buyer or seller can dispute
    seller = trade.get("seller", {})
    buyer = trade.get("buyer", {})
    if user.id not in (seller.get("user_id"), buyer.get("user_id")):
        await update.message.reply_text(
            "🚫 Only the assigned buyer or seller can open a dispute.",
            parse_mode="HTML",
        )
        return

    # Mark as disputed
    TradeModel.set_dispute(group_id=chat.id)

    await update.message.reply_text(
        dispute_opened_message(user.username or str(user.id)),
        parse_mode="HTML",
    )
