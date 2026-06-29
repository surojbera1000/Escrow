import os
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from pyrogram import Client

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")

# Pyrogram USER client (creates groups on behalf of your account)
# First run will ask for phone number + OTP code in terminal
# After that, session is saved and auto-logs in
user_client = Client(
    "escrow_user_session",
    api_id=API_ID,
    api_hash=API_HASH,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start command - shows the main menu."""
    text = (
        "creates a safe space for your\n"
        "escrow                                              /escrow\n\n"
        "know instructions                           /instructions\n\n"
        "assign yourself as a buyer                /buyer\n\n"
        "assign yourself as a seller                /seller\n\n"
        "get a deposit address                      /deposit\n\n"
        "know your trade balance                  /balance\n\n"
        "to release assets                              /release\n\n"
        "to refund assets                               /refund\n\n"
        "call an administrator                         /dispute\n\n"
        "save your address for future use       /save\n\n"
        "verify escrow address                       /verify"
    )

    keyboard = [[InlineKeyboardButton("START", callback_data="start_menu")]]
    await update.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))


async def start_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle START button press."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✅ Welcome! Use /escrow to create a new escrow deal.")


async def escrow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/escrow command - asks to select escrow type."""
    keyboard = [
        [
            InlineKeyboardButton("P2P", callback_data="escrow_type_p2p"),
            InlineKeyboardButton("Product Deal", callback_data="escrow_type_product"),
        ]
    ]
    await update.message.reply_text(
        text="Please select your escrow type from below.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def escrow_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle P2P or Product Deal button press - create group and show link."""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    # Get full name
    first = user.first_name or ""
    last = user.last_name or ""
    full_name = f"{first}{last}".strip() or user.username or "User"

    # Show loading message
    await query.edit_message_text(
        "⏳ Creating a safe trading place for you, please wait..."
    )

    try:
        # Create supergroup using the user session
        group = await user_client.create_supergroup(
            title="Escrow Group",
            description="P2P Crypto Escrow - Secure Trading Space"
        )
        chat_id = group.id

        # Add the bot to the group as admin
        bot_info = await context.bot.get_me()
        await user_client.add_chat_members(chat_id, bot_info.username)
        await asyncio.sleep(1)

        # Promote bot to admin
        await user_client.promote_chat_member(
            chat_id,
            bot_info.id,
            privileges=None  # Full admin
        )

        # Create invite link with member limit of 2
        invite = await user_client.create_chat_invite_link(
            chat_id=chat_id,
            member_limit=2,
            name="Escrow Invite"
        )
        link = invite.invite_link

        # Show success message
        await query.edit_message_text(
            f"Escrow Group Created\n\n"
            f"Creator: ⏤‌‌‌‌{full_name}\n\n"
            f"Join this escrow group and share the link with the buyer and seller.\n\n"
            f"{link}\n\n"
            f"⚠️ Note: This link is for 2 members only—third parties are not allowed to join."
        )

    except Exception as e:
        print(f"Group creation error: {e}")
        await query.edit_message_text(
            f"❌ Failed to create group.\n\n"
            f"Error: {str(e)}\n\n"
            f"Make sure your user session is logged in.\n"
            f"Restart the bot and enter phone + OTP if needed."
        )


async def post_init(application) -> None:
    """Start the Pyrogram user client when bot starts."""
    print("🔐 Starting user session...")
    print("   (First time: enter phone number + OTP in terminal)")
    await user_client.start()
    me = await user_client.get_me()
    print(f"✅ User session logged in as: {me.first_name} (@{me.username})")


async def post_shutdown(application) -> None:
    """Stop the Pyrogram user client when bot stops."""
    await user_client.stop()
    print("🔒 User session stopped.")


def main():
    if not BOT_TOKEN:
        print("ERROR: Set BOT_TOKEN in .env file")
        return

    if not API_ID or not API_HASH:
        print("ERROR: Set API_ID and API_HASH in .env file")
        print("Get them from https://my.telegram.org")
        return

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).post_shutdown(post_shutdown).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("escrow", escrow))
    app.add_handler(CallbackQueryHandler(start_button, pattern="^start_menu$"))
    app.add_handler(CallbackQueryHandler(escrow_type_selected, pattern="^escrow_type_"))

    print("✅ Bot running! Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
