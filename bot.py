import os
import asyncio
from io import BytesIO
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from pyrogram import Client
from pyrogram.types import ChatPrivileges
from pyrogram.enums import MessageServiceType
from PIL import Image, ImageDraw, ImageFont

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")

# Pyrogram USER client (creates groups on behalf of your account)
user_client = Client(
    "escrow_user_session",
    api_id=API_ID,
    api_hash=API_HASH,
)

# Pyrogram BOT client (used to delete service messages)
bot_client = Client(
    "escrow_bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
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


async def dd_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/dd command - shows deal details form."""
    await update.message.reply_text(
        "<b>Hello there,</b>\n"
        "<b>Kindly tell deal details i.e.</b>\n\n"
        "<code>Quantity -\n"
        "Rate -\n"
        "Conditions (if any) -</code>\n\n"
        "<b>Remember without it disputes wouldn't be resolved.</b> "
        "Once filled proceed with Specifications of the seller or buyer with "
        "/seller or /buyer [CRYPTO ADDRESS]",
        parse_mode="HTML"
    )


def generate_usage_image(command: str, example_address: str) -> BytesIO:
    """Generate an image showing how to use the /seller or /buyer command."""
    # Create image with dark background (like Telegram dark mode chat bubble)
    width, height = 700, 120
    img = Image.new("RGB", (width, height), color=(88, 86, 214))  # Purple/blue bubble color

    draw = ImageDraw.Draw(img)

    # Use default font (monospace-like)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 22)
    except Exception:
        font = ImageFont.load_default()

    # Draw command text
    draw.text((20, 20), f"/{command}", fill=(255, 255, 255), font=font)
    draw.text((20, 60), example_address, fill=(255, 255, 255), font=font)

    # Save to BytesIO
    bio = BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio


async def seller_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/seller command - if no address, show usage with photo. If address, declare role."""
    if not context.args:
        # No address provided - show usage image + text
        img = generate_usage_image("seller", "0x7a9521c4330d83aC2BeADCd17f88c7cE3FfC57d8")
        await update.message.reply_photo(
            photo=img,
            caption="/seller [Your Crypto Address]\n\n⛓️ Chains Supported: bsc, ltc, tron, btc",
        )
        return

    # Address provided
    wallet_address = context.args[0]
    user = update.effective_user
    username = user.username or user.first_name or "Unknown"
    chat_id = update.effective_chat.id

    # Check if this user already registered as buyer in this chat
    buyers = context.chat_data.get("buyers", {})
    if str(user.id) in buyers:
        await update.message.reply_text(
            "<b>Sorry! you are not allowed to use this command!</b>",
            parse_mode="HTML"
        )
        return

    # Check if seller is already set by another user
    sellers = context.chat_data.get("sellers", {})
    if sellers and str(user.id) not in sellers:
        # Another user already took seller role
        for uid in sellers:
            if uid != str(user.id):
                await update.message.reply_text(
                    "<b>Sorry! you are not allowed to use this command!</b>",
                    parse_mode="HTML"
                )
                return

    # Register as seller
    if "sellers" not in context.chat_data:
        context.chat_data["sellers"] = {}
    context.chat_data["sellers"][str(user.id)] = wallet_address
    context.chat_data[f"username_{user.id}"] = username

    # First message: Role declaration (reply to the user's message)
    await update.message.reply_text(
        "<b>📍ESCROW-ROLE DECLARATION</b>\n\n"
        f"<b>⚡️ SELLER @{username} | Userid: {user.id}</b>\n\n"
        "<b>✅ SELLER WALLET</b>\n"
        f"<code>{wallet_address}</code>\n\n"
        "<b>Note: If you don't see any address, then your address will used from saved addresses after selecting token and chain for the current escrow.</b>",
        parse_mode="HTML"
    )

    # Check if both roles are set - if yes, prompt /token
    buyers = context.chat_data.get("buyers", {})
    if buyers:
        await update.message.reply_text(
            "<b>Use /token to Choose crypto.</b>",
            parse_mode="HTML"
        )
    else:
        # Second message: Prompt to set buyer
        await update.message.reply_text(
            "<b>Please set buyer using /buyer [DEPOSIT ADDRESS]</b>",
            parse_mode="HTML"
        )


async def buyer_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/buyer command - if no address, show usage with photo. If address, declare role."""
    if not context.args:
        # No address provided - show usage image + text
        img = generate_usage_image("buyer", "0x7a9521c4330d83aC2BeADCd17f88c7cE3FfC57d8")
        await update.message.reply_photo(
            photo=img,
            caption="/buyer [Your Crypto Address]\n\n⛓️ Chains Supported: bsc, ltc, tron, btc",
        )
        return

    # Address provided
    wallet_address = context.args[0]
    user = update.effective_user
    username = user.username or user.first_name or "Unknown"
    chat_id = update.effective_chat.id

    # Check if this user already registered as seller in this chat
    sellers = context.chat_data.get("sellers", {})
    if str(user.id) in sellers:
        await update.message.reply_text(
            "<b>Sorry! you are not allowed to use this command!</b>",
            parse_mode="HTML"
        )
        return

    # Check if buyer is already set by another user
    buyers = context.chat_data.get("buyers", {})
    if buyers and str(user.id) not in buyers:
        # Another user already took buyer role
        for uid in buyers:
            if uid != str(user.id):
                await update.message.reply_text(
                    "<b>Sorry! you are not allowed to use this command!</b>",
                    parse_mode="HTML"
                )
                return

    # Register as buyer
    if "buyers" not in context.chat_data:
        context.chat_data["buyers"] = {}
    context.chat_data["buyers"][str(user.id)] = wallet_address
    context.chat_data[f"username_{user.id}"] = username

    # First message: Role declaration (reply to the user's message)
    await update.message.reply_text(
        "<b>📍ESCROW-ROLE DECLARATION</b>\n\n"
        f"<b>⚡️ BUYER @{username} | Userid: {user.id}</b>\n\n"
        "<b>✅ BUYER WALLET</b>\n"
        f"<code>{wallet_address}</code>\n\n"
        "<b>Note: If you don't see any address, then your address will used from saved addresses after selecting token and chain for the current escrow.</b>",
        parse_mode="HTML"
    )

    # Check if both roles are set - if yes, prompt /token
    sellers = context.chat_data.get("sellers", {})
    if sellers:
        await update.message.reply_text(
            "<b>Use /token to Choose crypto.</b>",
            parse_mode="HTML"
        )
    else:
        # Second message: Prompt to set seller
        await update.message.reply_text(
            "<b>Please set seller using /seller [DEPOSIT ADDRESS]</b>",
            parse_mode="HTML"
        )


async def token_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/token command - show token selection buttons."""
    user = update.effective_user
    # Store who initiated /token
    context.chat_data["token_initiator_id"] = str(user.id)

    keyboard = [
        [
            InlineKeyboardButton("LTC", callback_data="token_LTC"),
            InlineKeyboardButton("BTC", callback_data="token_BTC"),
        ],
        [
            InlineKeyboardButton("USDT", callback_data="token_USDT"),
        ],
    ]
    await update.message.reply_text(
        "*choose token from the list below*",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def escrow_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle P2P or Product Deal button press - create group and show link."""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    first = user.first_name or ""
    last = user.last_name or ""
    full_name = f"{first}{last}".strip() or user.username or "User"

    # Determine group name based on selection
    if "p2p" in query.data:
        group_title = "P2P Escrow By PAGAL Bot"
    else:
        group_title = "OTC Escrow By PAGAL Bot"

    # Show loading message (bold)
    await query.edit_message_text(
        "<b>⏳ Creating a safe trading place for you, please wait...</b>",
        parse_mode="HTML"
    )

    try:
        # Step 1: User session creates supergroup
        group = await user_client.create_supergroup(
            title=group_title,
            description="Secure Escrow Trading Space"
        )
        chat_id = group.id

        # Step 2: Add bot to the group
        bot_info = await context.bot.get_me()
        bot_uname = BOT_USERNAME or bot_info.username
        await user_client.add_chat_members(chat_id, bot_uname)
        await asyncio.sleep(1)

        # Step 3: Promote bot to admin with full privileges
        await user_client.promote_chat_member(
            chat_id,
            bot_info.id,
            privileges=ChatPrivileges(
                can_manage_chat=True,
                can_post_messages=True,
                can_edit_messages=True,
                can_delete_messages=True,
                can_restrict_members=True,
                can_promote_members=True,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_manage_video_chats=True,
            )
        )
        await asyncio.sleep(1)

        # Step 4: Create invite link with member limit of 2
        invite = await user_client.create_chat_invite_link(
            chat_id=chat_id,
            member_limit=2,
            name="Escrow Invite"
        )
        link = invite.invite_link

        # Step 5: User session leaves the group
        await user_client.leave_chat(chat_id)
        await asyncio.sleep(2)

        # Step 6: Bot deletes ALL messages in the group (removes join/left history completely)
        try:
            msg_ids = []
            async for msg in bot_client.get_chat_history(chat_id, limit=100):
                msg_ids.append(msg.id)
            if msg_ids:
                await bot_client.delete_messages(chat_id, msg_ids)
        except Exception:
            pass

        # Step 7: Bot sends welcome message (BOLD)
        await context.bot.send_message(
            chat_id=chat_id,
            text="<b>📍 Hey there traders! Welcome to our escrow service.</b>\n<b>✅ Please start with /dd command and fill the DealInfo Form</b>",
            parse_mode="HTML"
        )

        # Show success message to user in DM (bold)
        await query.edit_message_text(
            f"<b>Escrow Group Created</b>\n\n"
            f"<b>Creator: ⏤‌‌‌‌{full_name}</b>\n\n"
            f"<b>Join this escrow group and share the link with the buyer and seller.</b>\n\n"
            f"{link}\n\n"
            f"<b>⚠️ Note: This link is for 2 members only—third parties are not allowed to join.</b>",
            parse_mode="HTML"
        )

    except Exception as e:
        print(f"Group creation error: {e}")
        await query.edit_message_text(
            f"❌ Failed to create group.\n\n"
            f"Error: {str(e)}\n\n"
            f"Make sure your user session is logged in.\n"
            f"Restart the bot and enter phone + OTP if needed."
        )


async def token_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle token button press (LTC, BTC, USDT)."""
    query = update.callback_query
    await query.answer()

    token = query.data.replace("token_", "")  # LTC, BTC, USDT
    context.chat_data["selected_token"] = token

    if token == "USDT":
        # USDT has network selection
        keyboard = [
            [
                InlineKeyboardButton("BSC[BEP20]", callback_data="network_BSC"),
                InlineKeyboardButton("TRON[TRC20]", callback_data="network_TRON"),
            ],
            [
                InlineKeyboardButton("Back ⬅️", callback_data="network_back"),
            ],
        ]
        text = (
            "*📌 ESCROW\\-CRYPTO DECLARATION*\n\n"
            "*✅ CRYPTO*\n"
            "`USDT`\n\n"
            "`choose network from the list below for USDT`"
        )
        await query.edit_message_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    elif token == "LTC":
        context.chat_data["selected_network"] = "Litecoin"
        text = (
            "*📌 ESCROW\\-CRYPTO DECLARATION*\n\n"
            "*✅ CRYPTO*\n"
            "`LTC`\n\n"
            "*✅ NETWORK*\n"
            "`Litecoin`"
        )
        await query.edit_message_text(
            text,
            parse_mode="MarkdownV2",
        )
        await send_declaration_summary(query, context)
    elif token == "BTC":
        context.chat_data["selected_network"] = "Bitcoin"
        text = (
            "*📌 ESCROW\\-CRYPTO DECLARATION*\n\n"
            "*✅ CRYPTO*\n"
            "`BTC`\n\n"
            "*✅ NETWORK*\n"
            "`Bitcoin`"
        )
        await query.edit_message_text(
            text,
            parse_mode="MarkdownV2",
        )
        await send_declaration_summary(query, context)


async def network_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle network button press (BSC, TRON, Back)."""
    query = update.callback_query
    await query.answer()

    network = query.data.replace("network_", "")  # BSC, TRON, back

    if network == "back":
        # Go back to token selection
        keyboard = [
            [
                InlineKeyboardButton("LTC", callback_data="token_LTC"),
                InlineKeyboardButton("BTC", callback_data="token_BTC"),
            ],
            [
                InlineKeyboardButton("USDT", callback_data="token_USDT"),
            ],
        ]
        await query.edit_message_text(
            "*choose token from the list below*",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    # Set network name
    if network == "BSC":
        context.chat_data["selected_network"] = "BSC"
    else:
        context.chat_data["selected_network"] = "TRON"

    token = context.chat_data.get("selected_token", "USDT")
    network_display = context.chat_data["selected_network"]

    text = (
        "*📌 ESCROW\\-CRYPTO DECLARATION*\n\n"
        "*✅ CRYPTO*\n"
        f"`{token}`\n\n"
        "*✅ NETWORK*\n"
        f"`{network_display}`"
    )
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
    )

    # Send declaration summary for opponent to confirm
    await send_declaration_summary(query, context)


async def send_declaration_summary(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the escrow declaration summary for the OPPONENT to confirm.
    
    Logic:
    - If SELLER initiated /token → opponent is BUYER → show "Buyer @username"
    - If BUYER initiated /token → opponent is SELLER → show "Seller @username"
    Only the opponent can tap Accept/Reject.
    """
    chat_id = query.message.chat_id
    token = context.chat_data.get("selected_token", "")
    network = context.chat_data.get("selected_network", "")

    # Determine who initiated /token
    initiator_id = context.chat_data.get("token_initiator_id", "")

    # Find the opponent
    buyers = context.chat_data.get("buyers", {})
    sellers = context.chat_data.get("sellers", {})

    opponent_username = "Unknown"
    opponent_id = "Unknown"
    opponent_role = "Buyer"  # default

    # If initiator is seller → opponent is buyer
    if initiator_id in sellers:
        opponent_role = "Buyer"
        for uid, wallet in buyers.items():
            opponent_id = uid
            opponent_username = context.chat_data.get(f"username_{uid}", "Unknown")
            break
    # If initiator is buyer → opponent is seller
    elif initiator_id in buyers:
        opponent_role = "Seller"
        for uid, wallet in sellers.items():
            opponent_id = uid
            opponent_username = context.chat_data.get(f"username_{uid}", "Unknown")
            break

    # Store opponent ID and role for button validation
    context.chat_data["declaration_opponent_id"] = opponent_id
    context.chat_data["declaration_opponent_role"] = opponent_role
    context.chat_data["declaration_opponent_username"] = opponent_username

    keyboard = [
        [
            InlineKeyboardButton("Accept ✅", callback_data="declaration_accept"),
            InlineKeyboardButton("Reject ❌", callback_data="declaration_reject"),
        ]
    ]

    # Escape special characters for MarkdownV2
    def escape_md(text):
        special = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special:
            text = text.replace(char, f'\\{char}')
        return text

    opp_user_escaped = escape_md(opponent_username)
    opp_id_escaped = escape_md(str(opponent_id))
    token_escaped = escape_md(token)
    network_escaped = escape_md(network)
    role_escaped = escape_md(opponent_role)

    text = (
        f"*📌 ESCROW DECLARATION*\n\n"
        f"*⚡ {role_escaped} @{opp_user_escaped} \\| Userid: \\[{opp_id_escaped}\\]*\n\n"
        f"*✅ {token_escaped} CRYPTO*\n"
        f"*✅ {network_escaped} NETWORK*"
    )

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def declaration_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Accept/Reject button - only opponent can tap."""
    query = update.callback_query
    user = query.from_user

    # Check if this user is the opponent (only they can accept/reject)
    opponent_id = context.chat_data.get("declaration_opponent_id", "")
    if str(user.id) != str(opponent_id):
        await query.answer("❌ Only the opponent can confirm this declaration!", show_alert=True)
        return

    await query.answer()

    token = context.chat_data.get("selected_token", "")
    network = context.chat_data.get("selected_network", "")
    opponent_role = context.chat_data.get("declaration_opponent_role", "Buyer")
    username = user.username or user.first_name or "Unknown"

    def escape_md(text):
        special = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special:
            text = text.replace(char, f'\\{char}')
        return text

    user_escaped = escape_md(username)
    uid_escaped = escape_md(str(user.id))
    token_escaped = escape_md(token)
    network_escaped = escape_md(network)
    role_escaped = escape_md(opponent_role)

    if query.data == "declaration_accept":
        text = (
            f"*📌 ESCROW DECLARATION*\n\n"
            f"*⚡ {role_escaped} @{user_escaped} \\| Userid: \\[{uid_escaped}\\]*\n\n"
            f"*✅ {token_escaped} CRYPTO*\n"
            f"*✅ {network_escaped} NETWORK*\n\n"
            f"*✅ ACCEPTED*"
        )
        await query.edit_message_text(text, parse_mode="MarkdownV2")
        context.chat_data["declaration_accepted"] = True

    elif query.data == "declaration_reject":
        text = (
            f"*📌 ESCROW DECLARATION*\n\n"
            f"*⚡ {role_escaped} @{user_escaped} \\| Userid: \\[{uid_escaped}\\]*\n\n"
            f"*❌ REJECTED*\n\n"
            f"*Use /token to try again\\.*"
        )
        await query.edit_message_text(text, parse_mode="MarkdownV2")
        context.chat_data["declaration_accepted"] = False


async def post_init(application) -> None:
    """Start Pyrogram clients when bot starts."""
    print("🔐 Starting user session...")
    print("   (First time: enter phone number + OTP in terminal)")
    await user_client.start()
    me = await user_client.get_me()
    print(f"✅ User session logged in as: {me.first_name} (@{me.username})")

    print("🤖 Starting bot client...")
    await bot_client.start()
    print("✅ Bot client started.")


async def post_shutdown(application) -> None:
    """Stop Pyrogram clients when bot stops."""
    await bot_client.stop()
    await user_client.stop()
    print("🔒 Sessions stopped.")


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
    app.add_handler(CommandHandler("dd", dd_command))
    app.add_handler(CommandHandler("seller", seller_command))
    app.add_handler(CommandHandler("buyer", buyer_command))
    app.add_handler(CommandHandler("token", token_command))
    app.add_handler(CallbackQueryHandler(start_button, pattern="^start_menu$"))
    app.add_handler(CallbackQueryHandler(escrow_type_selected, pattern="^escrow_type_"))
    app.add_handler(CallbackQueryHandler(token_selected, pattern="^token_"))
    app.add_handler(CallbackQueryHandler(network_selected, pattern="^network_"))
    app.add_handler(CallbackQueryHandler(declaration_callback, pattern="^declaration_"))

    print("✅ Bot running! Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
