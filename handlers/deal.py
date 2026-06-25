"""
Handler for /dd (Deal Info) command and conversation flow.
Collects Quantity, Rate, and Conditions from the user.
"""

from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from utils.messages import deal_info_message, group_welcome_pin_message
from models.trade import TradeModel


# Conversation states
QUANTITY, RATE, CONDITIONS = range(3)


async def dd_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /dd command - start deal info collection."""
    chat = update.effective_chat

    # Only allow in groups
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text(
            "⚠️ This command can only be used in an escrow group.",
            parse_mode="HTML",
        )
        return ConversationHandler.END

    # Check if trade exists for this group
    trade = TradeModel.get_trade_by_group(chat.id)
    if not trade:
        # Create trade if bot was added to an existing group
        user = update.effective_user
        TradeModel.create_trade(
            group_id=chat.id,
            creator_id=user.id,
            creator_username=user.username or "",
        )

    await update.message.reply_text(
        "📝 <b>DEAL INFO FORM</b>\n\n"
        "Please provide the following details.\n\n"
        "💰 <b>Quantity</b> — Enter the trade amount:\n"
        "<i>(e.g., 100 USDT, 0.5 BTC)</i>",
        parse_mode="HTML",
    )
    return QUANTITY


async def quantity_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle quantity input."""
    context.user_data["deal_quantity"] = update.message.text.strip()

    await update.message.reply_text(
        "📊 <b>Rate</b> — Enter the exchange rate:\n"
        "<i>(e.g., 1 USDT = 85 INR, Market rate)</i>",
        parse_mode="HTML",
    )
    return RATE


async def rate_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle rate input."""
    context.user_data["deal_rate"] = update.message.text.strip()

    await update.message.reply_text(
        "📋 <b>Conditions</b> — Enter any conditions:\n"
        "<i>(e.g., Payment within 30 mins, or type 'none')</i>",
        parse_mode="HTML",
    )
    return CONDITIONS



async def conditions_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle conditions input and save deal info."""
    chat = update.effective_chat
    conditions = update.message.text.strip()
    quantity = context.user_data.get("deal_quantity", "N/A")
    rate = context.user_data.get("deal_rate", "N/A")

    # Save to database
    TradeModel.set_deal_info(
        group_id=chat.id,
        quantity=quantity,
        rate=rate,
        conditions=conditions,
    )

    # Send confirmation
    await update.message.reply_text(
        deal_info_message(quantity, rate, conditions),
        parse_mode="HTML",
    )

    # Cleanup user data
    context.user_data.pop("deal_quantity", None)
    context.user_data.pop("deal_rate", None)

    return ConversationHandler.END


async def cancel_deal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel deal info form."""
    await update.message.reply_text(
        "❌ Deal info form cancelled.",
        parse_mode="HTML",
    )
    context.user_data.pop("deal_quantity", None)
    context.user_data.pop("deal_rate", None)
    return ConversationHandler.END


def get_deal_conversation_handler() -> ConversationHandler:
    """Return the ConversationHandler for /dd command."""
    return ConversationHandler(
        entry_points=[CommandHandler("dd", dd_command)],
        states={
            QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, quantity_received)],
            RATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, rate_received)],
            CONDITIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, conditions_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel_deal)],
        per_chat=True,
        per_user=False,
    )
