"""
Handlers for /seller and /buyer role assignment commands.
"""

from telegram import Update
from telegram.ext import ContextTypes

from utils.messages import seller_declaration_card, buyer_declaration_card
from models.trade import TradeModel


async def seller_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /seller [WALLET_ADDRESS] command."""
    chat = update.effective_chat
    user = update.effective_user

    # Only allow in groups
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text(
            "⚠️ This command can only be used in an escrow group.",
            parse_mode="HTML",
        )
        return

    # Check for wallet address argument
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "⚠️ <b>Usage:</b> /seller [WALLET_ADDRESS]\n\n"
            "<i>Example: /seller 0x1234...abcd</i>",
            parse_mode="HTML",
        )
        return

    wallet_address = context.args[0].strip()

    # Validate wallet address (basic check)
    if len(wallet_address) < 20:
        await update.message.reply_text(
            "❌ Invalid wallet address. Please provide a valid address.",
            parse_mode="HTML",
        )
        return

    # Check if trade exists
    trade = TradeModel.get_trade_by_group(chat.id)
    if not trade:
        await update.message.reply_text(
            "⚠️ No active trade in this group. Use /dd first.",
            parse_mode="HTML",
        )
        return

    # Check if seller is already assigned
    if trade.get("seller") and trade["seller"]["user_id"] != user.id:
        await update.message.reply_text(
            "⚠️ A seller has already been assigned to this trade.",
            parse_mode="HTML",
        )
        return


    # Check user is not already the buyer
    if trade.get("buyer") and trade["buyer"]["user_id"] == user.id:
        await update.message.reply_text(
            "❌ You are already assigned as the Buyer. Cannot be both.",
            parse_mode="HTML",
        )
        return

    # Save seller to database
    TradeModel.set_seller(
        group_id=chat.id,
        user_id=user.id,
        username=user.username or str(user.id),
        wallet_address=wallet_address,
    )

    # Send declaration card
    await update.message.reply_text(
        seller_declaration_card(
            username=user.username or str(user.id),
            user_id=user.id,
            wallet_address=wallet_address,
        ),
        parse_mode="HTML",
    )


async def buyer_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /buyer [WALLET_ADDRESS] command."""
    chat = update.effective_chat
    user = update.effective_user

    # Only allow in groups
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text(
            "⚠️ This command can only be used in an escrow group.",
            parse_mode="HTML",
        )
        return

    # Check for wallet address argument
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "⚠️ <b>Usage:</b> /buyer [WALLET_ADDRESS]\n\n"
            "<i>Example: /buyer 0x1234...abcd</i>",
            parse_mode="HTML",
        )
        return

    wallet_address = context.args[0].strip()

    # Validate wallet address (basic check)
    if len(wallet_address) < 20:
        await update.message.reply_text(
            "❌ Invalid wallet address. Please provide a valid address.",
            parse_mode="HTML",
        )
        return

    # Check if trade exists
    trade = TradeModel.get_trade_by_group(chat.id)
    if not trade:
        await update.message.reply_text(
            "⚠️ No active trade in this group. Use /dd first.",
            parse_mode="HTML",
        )
        return

    # Check if buyer is already assigned
    if trade.get("buyer") and trade["buyer"]["user_id"] != user.id:
        await update.message.reply_text(
            "⚠️ A buyer has already been assigned to this trade.",
            parse_mode="HTML",
        )
        return

    # Check user is not already the seller
    if trade.get("seller") and trade["seller"]["user_id"] == user.id:
        await update.message.reply_text(
            "❌ You are already assigned as the Seller. Cannot be both.",
            parse_mode="HTML",
        )
        return

    # Save buyer to database
    TradeModel.set_buyer(
        group_id=chat.id,
        user_id=user.id,
        username=user.username or str(user.id),
        wallet_address=wallet_address,
    )

    # Send declaration card
    await update.message.reply_text(
        buyer_declaration_card(
            username=user.username or str(user.id),
            user_id=user.id,
            wallet_address=wallet_address,
        ),
        parse_mode="HTML",
    )
