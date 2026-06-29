import os
import asyncio
import random
import hashlib
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from pyrogram import Client
from pyrogram.types import ChatPrivileges
from pyrogram.enums import MessageServiceType
from pyrogram import raw
from PIL import Image, ImageDraw, ImageFont

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")

# Template file_id from PAGAL Escrow Bot style image (auto-downloads on first run)
TEMPLATE_FILE_ID = os.getenv("TEMPLATE_FILE_ID", "AgACAgUAAxkBAAFNwkdqQlazoGrOAwhY04Ymi31W9HW6kwACthBrG-VpGFZFi7z7BxhCNAEAAwIAA3kAAzwE")

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
    """/token command - show token selection buttons. Reply to user's /token message."""
    user = update.effective_user
    # Store who initiated /token and the message ID to reply to
    context.chat_data["token_initiator_id"] = str(user.id)
    context.chat_data["token_message_id"] = update.message.message_id

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
        reply_to_message_id=update.message.message_id,
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

        # Step 4.5: Set chat history hidden for new members (private)
        try:
            await user_client.invoke(
                raw.functions.messages.TogglePreHistoryHidden(
                    peer=await user_client.resolve_peer(chat_id),
                    enabled=True
                )
            )
        except Exception:
            pass

        # Step 5: User session leaves the group
        await user_client.leave_chat(chat_id)
        await asyncio.sleep(3)

        # Step 6: Bot deletes ALL messages in the group (removes join/left history completely)
        # Try multiple times to ensure the "left" service message is caught
        for attempt in range(3):
            try:
                msg_ids = []
                async for msg in bot_client.get_chat_history(chat_id, limit=100):
                    msg_ids.append(msg.id)
                if msg_ids:
                    await bot_client.delete_messages(chat_id, msg_ids)
                    break
            except Exception:
                await asyncio.sleep(1)

        # Step 7: Bot sends welcome message and PINS it
        keyboard = [[InlineKeyboardButton("How To Use Bot ?", url="https://t.me/how_to_use_pagalescrowbot")]]

        welcome_msg = await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "Hello there,\n"
                "Kindly tell deal details i.e.\n\n"
                "<code>Quantity -</code>\n"
                "<code>Rate -</code>\n"
                "<code>Conditions (if any) -</code>\n\n"
                "Remember without it disputes wouldn't be resolved. "
                "Once filled proceed with Specifications of the seller or buyer with "
                "<code>/seller</code> or <code>/buyer</code> <b>[CRYPTO ADDRESS]</b>"
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        # Pin the welcome message
        try:
            await context.bot.pin_chat_message(
                chat_id=chat_id,
                message_id=welcome_msg.message_id,
                disable_notification=True
            )
        except Exception:
            pass

        # Delete the "pinned message" service notification
        await asyncio.sleep(1)
        try:
            async for msg in bot_client.get_chat_history(chat_id, limit=5):
                if msg.service and msg.id != welcome_msg.message_id:
                    await bot_client.delete_messages(chat_id, msg.id)
        except Exception:
            pass

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
        await edit_to_declaration(query, context)
    elif token == "BTC":
        context.chat_data["selected_network"] = "Bitcoin"
        await edit_to_declaration(query, context)


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

    # Merge everything into one message with Accept/Reject buttons
    await edit_to_declaration(query, context)


async def edit_to_declaration(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Edit the current message to show full ESCROW DECLARATION with Accept/Reject buttons.
    
    This merges everything into ONE message (like the screenshot).
    """
    token = context.chat_data.get("selected_token", "")
    network = context.chat_data.get("selected_network", "")

    # Determine who initiated /token
    initiator_id = context.chat_data.get("token_initiator_id", "")

    # Find the opponent
    buyers = context.chat_data.get("buyers", {})
    sellers = context.chat_data.get("sellers", {})

    opponent_username = "Unknown"
    opponent_id = "Unknown"
    opponent_role = "Buyer"

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

    # Edit the SAME message (merge) with Accept/Reject buttons
    await query.edit_message_text(
        text,
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

        # Now send TRANSACTION INFORMATION message
        await send_transaction_info(query, context)

    elif query.data == "declaration_reject":
        text = (
            f"*📌 ESCROW DECLARATION*\n\n"
            f"*⚡ {role_escaped} @{user_escaped} \\| Userid: \\[{uid_escaped}\\]*\n\n"
            f"*❌ REJECTED*\n\n"
            f"*Use /token to try again\\.*"
        )
        await query.edit_message_text(text, parse_mode="MarkdownV2")
        context.chat_data["declaration_accepted"] = False


async def send_transaction_info(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send TRANSACTION INFORMATION after Accept, change group photo, check bio for fees."""
    chat_id = query.message.chat_id
    token = context.chat_data.get("selected_token", "")
    network = context.chat_data.get("selected_network", "")

    # Get seller info
    sellers = context.chat_data.get("sellers", {})
    seller_username = "Unknown"
    seller_id = "Unknown"
    seller_wallet = "Unknown"
    for uid, wallet in sellers.items():
        seller_id = uid
        seller_username = context.chat_data.get(f"username_{uid}", "Unknown")
        seller_wallet = wallet
        break

    # Get buyer info
    buyers = context.chat_data.get("buyers", {})
    buyer_username = "Unknown"
    buyer_id = "Unknown"
    buyer_wallet = "Unknown"
    for uid, wallet in buyers.items():
        buyer_id = uid
        buyer_username = context.chat_data.get(f"username_{uid}", "Unknown")
        buyer_wallet = wallet
        break

    # Generate transaction ID
    txn_id = str(random.randint(10000000, 99999999))
    context.chat_data["transaction_id"] = txn_id

    # Current date and time
    now = datetime.now()
    trade_date = now.strftime("%d/%m/%Y")
    trade_time = now.strftime("%I:%M %p")

    # Send Transaction Information message
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"<b>📍 TRANSACTION INFORMATION [{txn_id}]</b>\n\n"
            f"<b>⚡️ SELLER</b>\n"
            f"<b>@{seller_username} | [{seller_id}]</b>\n"
            f"{seller_wallet} [{token}] [{network}]\n\n"
            f"<b>⚡️ BUYER</b>\n"
            f"<b>@{buyer_username} | [{buyer_id}]</b>\n"
            f"{buyer_wallet} [{token}] [{network}]\n\n"
            f"<b>⏰ Trade Start Time: {trade_date} {trade_time}</b>\n\n\n"
            f"<b>⚠️ IMPORTANT: Make sure to finalise and agree each-others terms before depositing.</b>\n\n"
            f"<b>🗒 Please use /deposit command to generate a deposit address for your trade.</b>"
        ),
        parse_mode="HTML",
    )

    # Change group photo matching the PAGAL Escrow Bot style
    try:
        # Try to use saved template image, draw usernames on it
        template_path = os.path.join(os.path.dirname(__file__), "template.png")

        if os.path.exists(template_path):
            # Load template and draw usernames
            img = Image.open(template_path).copy()
            img = img.resize((800, 800))
            draw = ImageDraw.Draw(img)

            try:
                font_names = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
            except Exception:
                font_names = ImageFont.load_default()

            # Draw BUYER and SELLER usernames (matching screenshot positions)
            draw.text((280, 490), f"@{buyer_username}", fill=(255, 255, 255), font=font_names)
            draw.text((280, 580), f"@{seller_username}", fill=(255, 255, 255), font=font_names)

        else:
            # Fallback: generate image from scratch (PAGAL style)
            img = Image.new("RGB", (800, 800), color=(20, 20, 20))
            draw = ImageDraw.Draw(img)

            try:
                font_pagal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
                font_escrow = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
                font_names = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
                font_dollar = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 60)
            except Exception:
                font_pagal = ImageFont.load_default()
                font_escrow = ImageFont.load_default()
                font_names = ImageFont.load_default()
                font_dollar = ImageFont.load_default()

            # Draw $ signs as background pattern
            for row in range(0, 800, 120):
                for col in range(0, 800, 120):
                    draw.text((col + 15, row + 15), "$", fill=(0, 80, 0), font=font_dollar)

            # Green rectangle for P.A.G.A.L
            draw.rectangle([(250, 80), (550, 155)], fill=(34, 139, 34))
            draw.text((272, 88), "P.A.G.A.L", fill=(255, 255, 255), font=font_pagal)

            # ESCROW BOT text
            draw.text((170, 190), "ESCROW BOT", fill=(255, 255, 255), font=font_escrow)

            # 💰 BUYER: @username
            draw.text((80, 420), f"\U0001f4b0 BUYER:", fill=(0, 200, 80), font=font_names)
            draw.text((320, 420), f"@{buyer_username}", fill=(255, 255, 255), font=font_names)

            # 💰 SELLER: @username
            draw.text((80, 510), f"\U0001f4b0 SELLER:", fill=(0, 200, 80), font=font_names)
            draw.text((320, 510), f"@{seller_username}", fill=(255, 255, 255), font=font_names)

        bio = BytesIO()
        img.save(bio, format="PNG")
        bio.seek(0)

        await context.bot.set_chat_photo(chat_id=chat_id, photo=bio)
    except Exception as e:
        print(f"Failed to set group photo: {e}")

    # Check bio for @PagaLEscrowBot
    bot_me = await context.bot.get_me()
    bot_username_check = bot_me.username  # e.g. "PagaLEscrowBot"

    seller_has_bio = False
    buyer_has_bio = False

    try:
        # Check seller's bio using Pyrogram bot client
        seller_info = await bot_client.get_users(int(seller_id))
        if seller_info and seller_info.bio:
            if f"@{bot_username_check}".lower() in seller_info.bio.lower():
                seller_has_bio = True
    except Exception:
        pass

    try:
        # Check buyer's bio using Pyrogram bot client
        buyer_info = await bot_client.get_users(int(buyer_id))
        if buyer_info and buyer_info.bio:
            if f"@{bot_username_check}".lower() in buyer_info.bio.lower():
                buyer_has_bio = True
    except Exception:
        pass

    # Send fee message based on bio check
    if seller_has_bio and buyer_has_bio:
        fee_text = (
            f"<b>Your Fee is 0.25% as both buyer and seller are using "
            f"@{bot_username_check} in your bio.</b>"
        )
    else:
        fee_text = (
            f"<b>Your Fee is 1.0% as both buyer and seller are not using "
            f"@{bot_username_check} in your bio.</b>"
        )

    await context.bot.send_message(
        chat_id=chat_id,
        text=fee_text,
        parse_mode="HTML",
    )


async def deposit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/deposit command - generate deposit address and show transaction info."""
    chat_id = update.effective_chat.id
    token = context.chat_data.get("selected_token", "")
    network = context.chat_data.get("selected_network", "")

    # Check if declaration was accepted
    if not context.chat_data.get("declaration_accepted"):
        await update.message.reply_text(
            "<b>⚠️ Please complete the token/network selection and get acceptance first.</b>",
            parse_mode="HTML"
        )
        return

    # Get seller info
    sellers = context.chat_data.get("sellers", {})
    seller_username = "Unknown"
    seller_id = "Unknown"
    for uid, wallet in sellers.items():
        seller_id = uid
        seller_username = context.chat_data.get(f"username_{uid}", "Unknown")
        break

    # Get buyer info
    buyers = context.chat_data.get("buyers", {})
    buyer_username = "Unknown"
    buyer_id = "Unknown"
    for uid, wallet in buyers.items():
        buyer_id = uid
        buyer_username = context.chat_data.get(f"username_{uid}", "Unknown")
        break

    # Fixed escrow address
    escrow_address = "0xf5CDdbB7d687289aDfF413A48C7f1881910e6925"

    txn_id = context.chat_data.get("transaction_id", str(random.randint(10000000, 99999999)))
    context.chat_data["escrow_address"] = escrow_address
    context.chat_data["deposit_start_time"] = datetime.now().timestamp()

    # Current date and time
    now = datetime.now()
    trade_date = now.strftime("%d/%m/%Y")
    trade_time = now.strftime("%I:%M %p")

    # First message: loading
    await update.message.reply_text(
        "<b>Requesting a deposit address for you, please wait...</b>",
        parse_mode="HTML"
    )

    await asyncio.sleep(2)

    # Second message: full deposit info with Check Payment button
    keyboard = [[InlineKeyboardButton("Check Payment", callback_data="check_payment")]]

    deposit_text = (
        f"<b>📍 TRANSACTION INFORMATION [{txn_id}]</b>\n\n"
        f"<b>⚡️ SELLER</b>\n"
        f"<b>@{seller_username} | [{seller_id}]</b>\n"
        f"<b>⚡️ BUYER</b>\n"
        f"<b>@{buyer_username} | [{buyer_id}]</b>\n"
        f"<b>🟢 ESCROW ADDRESS</b>\n"
        f"<code>{escrow_address}</code>\n"
        f"<b>[{token}] [{network}]</b>\n\n"
        f"<b>Seller @{seller_username} Will Pay on the Escrow Address, And Click On Check Payment.</b>\n\n"
        f"<b>Amount Recieved:</b> <code>0.00000</code> <b>[0.00$]</b>\n\n"
        f"<b>⏰ Trade Start Time: {trade_date} {trade_time}</b>\n"
        f"<b>⏰ Address Reset In: 20.00 Min</b>\n\n"
        f"<b>📄 Note: Address will reset after the given time, so make sure to deposit in the bot before the address exprires.</b>\n"
        f"<b>Useful commands:</b>\n"
        f"<b>🗒</b> <code>/release</code><b>= Will Release The Funds To Buyer.</b>\n"
        f"<b>🗒</b> <code>/refund</code><b>= Will Refund The Funds To Seller.</b>\n\n"
        f"<b>Remember, once commands are used payment will be released, there is no revert!</b>"
    )

    msg = await update.message.reply_text(
        deposit_text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    # Store deposit message ID for updating countdown
    context.chat_data["deposit_message_id"] = msg.message_id
    context.chat_data["deposit_chat_id"] = chat_id


async def check_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Check Payment button - update the countdown timer."""
    query = update.callback_query
    await query.answer("🔍 Checking payment...")

    chat_id = query.message.chat_id
    token = context.chat_data.get("selected_token", "")
    network = context.chat_data.get("selected_network", "")
    txn_id = context.chat_data.get("transaction_id", "00000000")
    escrow_address = context.chat_data.get("escrow_address", "")
    deposit_start = context.chat_data.get("deposit_start_time", datetime.now().timestamp())

    # Get seller info
    sellers = context.chat_data.get("sellers", {})
    seller_username = "Unknown"
    seller_id = "Unknown"
    for uid, wallet in sellers.items():
        seller_id = uid
        seller_username = context.chat_data.get(f"username_{uid}", "Unknown")
        break

    # Get buyer info
    buyers = context.chat_data.get("buyers", {})
    buyer_username = "Unknown"
    buyer_id = "Unknown"
    for uid, wallet in buyers.items():
        buyer_id = uid
        buyer_username = context.chat_data.get(f"username_{uid}", "Unknown")
        break

    # Calculate remaining time
    elapsed = datetime.now().timestamp() - deposit_start
    remaining_min = max(0, 20.0 - (elapsed / 60))

    # Current date and time
    now = datetime.now()
    trade_date = now.strftime("%d/%m/%Y")
    trade_time = now.strftime("%I:%M %p")

    keyboard = [[InlineKeyboardButton("Check Payment", callback_data="check_payment")]]

    deposit_text = (
        f"<b>📍 TRANSACTION INFORMATION [{txn_id}]</b>\n\n"
        f"<b>⚡️ SELLER</b>\n"
        f"<b>@{seller_username} | [{seller_id}]</b>\n"
        f"<b>⚡️ BUYER</b>\n"
        f"<b>@{buyer_username} | [{buyer_id}]</b>\n"
        f"<b>🟢 ESCROW ADDRESS</b>\n"
        f"<code>{escrow_address}</code>\n"
        f"<b>[{token}] [{network}]</b>\n\n"
        f"<b>Seller @{seller_username} Will Pay on the Escrow Address, And Click On Check Payment.</b>\n\n"
        f"<b>Amount Recieved:</b> <code>0.00000</code> <b>[0.00$]</b>\n\n"
        f"<b>⏰ Trade Start Time: {trade_date} {trade_time}</b>\n"
        f"<b>⏰ Address Reset In: {remaining_min:.2f} Min</b>\n\n"
        f"<b>📄 Note: Address will reset after the given time, so make sure to deposit in the bot before the address exprires.</b>\n"
        f"<b>Useful commands:</b>\n"
        f"<b>🗒</b> <code>/release</code><b>= Will Release The Funds To Buyer.</b>\n"
        f"<b>🗒</b> <code>/refund</code><b>= Will Refund The Funds To Seller.</b>\n\n"
        f"<b>Remember, once commands are used payment will be released, there is no revert!</b>"
    )

    await query.edit_message_text(
        deposit_text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def set_template_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/settemplate command - reply to a photo to set it as group photo template."""
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text(
            "<b>⚠️ Reply to a photo with /settemplate to save it as template.</b>",
            parse_mode="HTML"
        )
        return

    # Download the photo
    photo = update.message.reply_to_message.photo[-1]  # Largest size
    file = await context.bot.get_file(photo.file_id)
    template_path = os.path.join(os.path.dirname(__file__), "template.png")
    await file.download_to_drive(template_path)

    await update.message.reply_text(
        "<b>✅ Template saved! This will be used as group photo for new deals.</b>",
        parse_mode="HTML"
    )


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

    # Download template if not exists
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.png")
    if not os.path.exists(template_path) and TEMPLATE_FILE_ID:
        try:
            bot = application.bot
            file = await bot.get_file(TEMPLATE_FILE_ID)
            await file.download_to_drive(template_path)
            print(f"✅ Template downloaded from file_id")
        except Exception as e:
            print(f"⚠️ Could not download template: {e}")
            print("   Bot will generate group photo from scratch instead.")


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
    app.add_handler(CommandHandler("deposit", deposit_command))
    app.add_handler(CommandHandler("settemplate", set_template_command))
    app.add_handler(CallbackQueryHandler(start_button, pattern="^start_menu$"))
    app.add_handler(CallbackQueryHandler(escrow_type_selected, pattern="^escrow_type_"))
    app.add_handler(CallbackQueryHandler(token_selected, pattern="^token_"))
    app.add_handler(CallbackQueryHandler(network_selected, pattern="^network_"))
    app.add_handler(CallbackQueryHandler(declaration_callback, pattern="^declaration_"))
    app.add_handler(CallbackQueryHandler(check_payment_callback, pattern="^check_payment$"))

    print("✅ Bot running! Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
