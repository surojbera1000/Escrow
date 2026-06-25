"""
Handler for /escrow command.
Creates a new private escrow group, adds bot as admin, generates invite link.
"""

from telegram import Update
from telegram.ext import ContextTypes

from utils.messages import escrow_group_created_message, group_welcome_pin_message
from models.escrow_group import EscrowGroupModel
from models.trade import TradeModel


async def escrow_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /escrow command - create a new escrow group."""
    user = update.effective_user

    # Only allow in private chat
    if update.effective_chat.type != "private":
        await update.message.reply_text(
            "⚠️ Please use /escrow in a private chat with the bot.",
            parse_mode="HTML",
        )
        return

    await update.message.reply_text(
        "⏳ <b>Creating escrow group...</b>\nPlease wait.",
        parse_mode="HTML",
    )

    try:
        # Create a new supergroup for the escrow trade
        group_title = f"Escrow Trade - {user.first_name} #{user.id}"

        # Use createNewSupergroup via the bot API
        # Note: python-telegram-bot v20+ uses bot.create_new_sticker_set pattern
        # We use the raw API call for group creation
        result = await context.bot.create_chat(
            title=group_title,
            type="supergroup",
        )
        group_id = result.id

        # Set bot as admin (it already is as creator)
        # Generate invite link
        invite_link_obj = await context.bot.create_chat_invite_link(
            chat_id=group_id,
            name=f"Escrow-{user.id}",
        )
        invite_link = invite_link_obj.invite_link

        # Save to database
        EscrowGroupModel.create_group(
            group_id=group_id,
            creator_id=user.id,
            invite_link=invite_link,
            group_title=group_title,
        )

        # Create trade record
        TradeModel.create_trade(
            group_id=group_id,
            creator_id=user.id,
            creator_username=user.username or "",
        )

        # Pin welcome message in the group
        pin_msg = await context.bot.send_message(
            chat_id=group_id,
            text=group_welcome_pin_message(),
            parse_mode="HTML",
        )
        await context.bot.pin_chat_message(
            chat_id=group_id,
            message_id=pin_msg.message_id,
        )

        # Send invite link to user
        await update.message.reply_text(
            escrow_group_created_message(invite_link),
            parse_mode="HTML",
        )

    except Exception as e:
        # Fallback: If bot cannot create groups (API limitation),
        # provide alternative instructions
        await update.message.reply_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ <b>ESCROW GROUP SETUP</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Due to Telegram API limitations, please:\n\n"
            "1️⃣ Create a new group manually\n"
            f"2️⃣ Add @{context.bot.username} to the group\n"
            "3️⃣ Make the bot an <b>Administrator</b>\n"
            "4️⃣ Use /dd in the group to start the escrow\n\n"
            "The bot will automatically set up the escrow "
            "once added as an admin.\n\n"
            f"<i>Error details: {str(e)[:100]}</i>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="HTML",
        )
