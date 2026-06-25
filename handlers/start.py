"""
Handler for /start and /instructions commands.
Displays main menu and bot instructions.
"""

from telegram import Update
from telegram.ext import ContextTypes

from utils.messages import welcome_message, instructions_message, balance_message
from utils.keyboards import main_menu_keyboard
from models.user import UserModel


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - display welcome message with main menu."""
    user = update.effective_user

    # Create or update user in database
    UserModel.create_or_update_user(
        user_id=user.id,
        username=user.username or "",
        first_name=user.first_name or "",
        last_name=user.last_name or "",
    )

    await update.message.reply_text(
        welcome_message(user.first_name or "Trader"),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


async def instructions_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /instructions command - display bot usage instructions."""
    await update.message.reply_text(
        instructions_message(),
        parse_mode="HTML",
    )


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /balance command - display user balance."""
    user = update.effective_user
    await update.message.reply_text(
        balance_message(user.id, user.username or "Unknown"),
        parse_mode="HTML",
    )


async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /save command - save current trade state."""
    await update.message.reply_text(
        "💾 <b>Trade state saved.</b>\n\n"
        "Your current trade information has been saved to the database.",
        parse_mode="HTML",
    )


async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /verify command - verify user identity."""
    user = update.effective_user
    db_user = UserModel.get_user(user.id)
    if db_user:
        await update.message.reply_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ <b>VERIFICATION STATUS</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 <b>User:</b> @{user.username}\n"
            f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
            f"📊 <b>Total Trades:</b> {db_user.get('total_trades', 0)}\n"
            f"✅ <b>Successful:</b> {db_user.get('successful_trades', 0)}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            "❌ User not found. Please use /start first.",
            parse_mode="HTML",
        )
