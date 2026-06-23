"""/dd - the Deal Info Form (Quantity, Rate, Conditions) collected in-group."""

from __future__ import annotations

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from ..database import db
from ..utils import esc, is_group_chat

# Conversation states
ASK_QUANTITY, ASK_RATE, ASK_CONDITIONS = range(3)


async def dd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat = update.effective_chat
    message = update.effective_message

    if not is_group_chat(chat):
        await message.reply_text("The /dd Deal Info Form can only be filled inside an escrow group.")
        return ConversationHandler.END

    # Make sure a trade record exists for this group.
    trade = await db.get_trade(chat.id)
    if trade is None:
        await db.create_trade(chat_id=chat.id, creator_id=update.effective_user.id, invite_link="")

    context.user_data["dd"] = {}
    await message.reply_text(
        "\U0001f4dd <b>Deal Info Form</b>\n\nPlease enter the <b>Quantity -</b>",
        parse_mode=ParseMode.HTML,
    )
    return ASK_QUANTITY


async def dd_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.setdefault("dd", {})["quantity"] = update.effective_message.text.strip()
    await update.effective_message.reply_text("Please enter the <b>Rate -</b>", parse_mode=ParseMode.HTML)
    return ASK_RATE


async def dd_rate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.setdefault("dd", {})["rate"] = update.effective_message.text.strip()
    await update.effective_message.reply_text(
        "Please enter the <b>Conditions (if any) -</b>\n"
        "<i>(type \"none\" if there are no special conditions)</i>",
        parse_mode=ParseMode.HTML,
    )
    return ASK_CONDITIONS


async def dd_conditions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat = update.effective_chat
    data = context.user_data.setdefault("dd", {})
    data["conditions"] = update.effective_message.text.strip()

    await db.update_trade(chat.id, {"deal": data})

    summary = (
        "\u2705 <b>Deal Info Saved</b>\n\n"
        f"\U0001f4e6 <b>Quantity:</b> {esc(data.get('quantity'))}\n"
        f"\U0001f4b1 <b>Rate:</b> {esc(data.get('rate'))}\n"
        f"\U0001f4cb <b>Conditions:</b> {esc(data.get('conditions'))}\n\n"
        "Next: the seller and buyer should declare their roles with "
        "<code>/seller &lt;wallet&gt;</code> and <code>/buyer &lt;wallet&gt;</code>."
    )
    await update.effective_message.reply_text(summary, parse_mode=ParseMode.HTML)
    context.user_data.pop("dd", None)
    return ConversationHandler.END


async def dd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("dd", None)
    await update.effective_message.reply_text("Deal Info Form cancelled.")
    return ConversationHandler.END


def build_deal_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("dd", dd_start)],
        states={
            ASK_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, dd_quantity)],
            ASK_RATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, dd_rate)],
            ASK_CONDITIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, dd_conditions)],
        },
        fallbacks=[CommandHandler("cancel", dd_cancel)],
        per_user=True,
        per_chat=True,
        allow_reentry=True,
    )
