"""
Handler for /token command and InlineKeyboard callbacks.
Token selection (LTC, BTC, USDT) and network selection (BSC, TRON).
"""

from telegram import Update
from telegram.ext import ContextTypes

from utils.keyboards import (
    token_selection_keyboard,
    network_selection_keyboard,
    accept_reject_keyboard,
)
from utils.messages import escrow_declaration_card
from models.trade import TradeModel


async def token_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /token command - display token selection buttons."""
    chat = update.effective_chat

    # Only allow in groups
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text(
            "⚠️ This command can only be used in an escrow group.",
            parse_mode="HTML",
        )
        return

    # Check if trade exists and roles are assigned
    trade = TradeModel.get_trade_by_group(chat.id)
    if not trade:
        await update.message.reply_text(
            "⚠️ No active trade in this group. Use /dd first.",
            parse_mode="HTML",
        )
        return

    if not trade.get("seller") or not trade.get("buyer"):
        await update.message.reply_text(
            "⚠️ Both seller and buyer must be assigned first.\n"
            "Use /seller [WALLET] and /buyer [WALLET].",
            parse_mode="HTML",
        )
        return

    await update.message.reply_text(
        "💰 <b>SELECT TOKEN</b>\n\n"
        "Choose the cryptocurrency for this trade:",
        parse_mode="HTML",
        reply_markup=token_selection_keyboard(),
    )



async def token_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle token selection callback."""
    query = update.callback_query
    await query.answer()

    chat = update.effective_chat
    token = query.data.replace("token_", "")

    # Store selected token temporarily
    context.chat_data["selected_token"] = token

    await query.edit_message_text(
        f"💰 <b>Selected Token:</b> {token}\n\n"
        "🌐 <b>SELECT NETWORK</b>\n\n"
        "Choose the network for this trade:",
        parse_mode="HTML",
        reply_markup=network_selection_keyboard(token),
    )


async def network_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle network selection callback."""
    query = update.callback_query
    await query.answer()

    chat = update.effective_chat
    network = query.data.replace("network_", "")
    token = context.chat_data.get("selected_token", "USDT")

    # Save token and network to database
    TradeModel.set_token_network(
        group_id=chat.id,
        token=token,
        network=network,
    )

    # Get trade info for declaration card
    trade = TradeModel.get_trade_by_group(chat.id)
    if not trade or not trade.get("buyer"):
        await query.edit_message_text(
            "❌ Error: Trade or buyer information not found.",
            parse_mode="HTML",
        )
        return

    buyer = trade["buyer"]

    # Show escrow declaration card
    await query.edit_message_text(
        escrow_declaration_card(
            buyer_username=buyer["username"],
            buyer_id=buyer["user_id"],
            token=token,
            network=network,
        ),
        parse_mode="HTML",
        reply_markup=accept_reject_keyboard(),
    )
