"""
Handler for trade acceptance/rejection callbacks and /deposit command.
"""

from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from utils.messages import transaction_info_message, deposit_address_message
from utils.keyboards import check_payment_keyboard
from models.trade import TradeModel
from config.settings import (
    ESCROW_BSC_ADDRESS,
    ESCROW_TRON_ADDRESS,
    DEPOSIT_ADDRESS_TIMEOUT_MINUTES,
)


async def trade_accept_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle trade acceptance callback."""
    query = update.callback_query
    await query.answer()

    chat = update.effective_chat

    # Accept the trade
    TradeModel.accept_trade(group_id=chat.id)

    # Get updated trade info
    trade = TradeModel.get_trade_by_group(chat.id)
    if not trade:
        await query.edit_message_text("❌ Trade not found.", parse_mode="HTML")
        return

    seller = trade.get("seller", {})
    buyer = trade.get("buyer", {})
    token = trade.get("token", "USDT")
    network = trade.get("network", "BSC")
    start_time = trade.get("start_time", datetime.utcnow())

    # Edit message to show transaction info
    await query.edit_message_text(
        transaction_info_message(seller, buyer, token, network, start_time),
        parse_mode="HTML",
    )

    # Trigger group photo change
    await _change_group_photo(context, chat.id)



async def trade_reject_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle trade rejection callback."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "❌ <b>TRADE REJECTED</b>\n\n"
        "The escrow declaration has been rejected.\n"
        "Please discuss terms and try again with /token.",
        parse_mode="HTML",
    )


async def deposit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /deposit command - generate and display deposit address."""
    chat = update.effective_chat

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

    # Check trade is accepted
    if trade.get("status") not in ("accepted", "deposit_pending"):
        await update.message.reply_text(
            "⚠️ Trade must be accepted before generating deposit address.\n"
            "Use /token to select token and accept the trade.",
            parse_mode="HTML",
        )
        return

    # Determine deposit address based on network
    network = trade.get("network", "BSC")
    token = trade.get("token", "USDT")

    if network == "BSC":
        deposit_address = ESCROW_BSC_ADDRESS
    elif network == "TRON":
        deposit_address = ESCROW_TRON_ADDRESS
    else:
        deposit_address = ESCROW_BSC_ADDRESS  # Default fallback

    if not deposit_address:
        deposit_address = "0x_CONFIGURE_YOUR_ESCROW_WALLET_ADDRESS"

    # Save deposit address to trade
    TradeModel.set_deposit_address(group_id=chat.id, address=deposit_address)

    # Send deposit address with check payment button
    await update.message.reply_text(
        deposit_address_message(
            address=deposit_address,
            token=token,
            network=network,
            timeout_minutes=DEPOSIT_ADDRESS_TIMEOUT_MINUTES,
        ),
        parse_mode="HTML",
        reply_markup=check_payment_keyboard(),
    )


async def check_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle check payment button callback."""
    query = update.callback_query
    await query.answer("🔍 Checking payment status...")

    chat = update.effective_chat
    trade = TradeModel.get_trade_by_group(chat.id)

    if not trade:
        await query.answer("❌ No trade found.", show_alert=True)
        return

    amount_received = trade.get("amount_received", 0.0)
    token = trade.get("token", "USDT")

    if amount_received > 0:
        await query.edit_message_text(
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ <b>PAYMENT CONFIRMED</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💵 <b>Amount Received:</b> {amount_received:.5f} {token}\n\n"
            f"Funds are now held in escrow.\n"
            f"Seller can use /release to send funds to buyer.\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="HTML",
        )
    else:
        await query.answer(
            "⏳ No payment detected yet. Please wait and try again.",
            show_alert=True,
        )


async def _change_group_photo(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    """Change group photo after trade starts (group photo automation)."""
    import os
    from config.settings import GROUP_PHOTO_PATH

    if os.path.exists(GROUP_PHOTO_PATH):
        try:
            with open(GROUP_PHOTO_PATH, "rb") as photo_file:
                await context.bot.set_chat_photo(
                    chat_id=chat_id,
                    photo=photo_file,
                )
        except Exception:
            pass  # Silently fail - photo is a bonus feature
