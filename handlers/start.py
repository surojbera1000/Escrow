"""
Start command handler for the Escrow Bot.
Handles /start command and the START button callback.
Matches the exact layout from the PAGAL Escrow Bot screenshot.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils.keyboards import start_keyboard
from utils.formatting import format_start_message


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command - show welcome message and menu.
    Replicates the exact PAGAL Escrow Bot start menu layout.
    """
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
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        text=text,
        reply_markup=reply_markup,
    )


async def start_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the START button press."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        text=(
            "🚀 <b>Welcome to P2P Crypto Escrow Bot!</b>\n\n"
            "Use /escrow to create a new escrow deal.\n\n"
            "📋 <b>Quick Guide:</b>\n"
            "1️⃣ Create escrow with /escrow\n"
            "2️⃣ Join the escrow group\n"
            "3️⃣ Fill deal details with /dd\n"
            "4️⃣ Declare roles: /seller & /buyer\n"
            "5️⃣ Select token with /token\n"
            "6️⃣ Deposit with /deposit\n"
            "7️⃣ Release or refund when ready\n\n"
            "💡 Type /help for more information."
        ),
        parse_mode="HTML",
    )


async def instructions_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /instructions command - show detailed instructions."""
    await update.message.reply_text(
        text=(
            "📖 <b>HOW TO USE THIS BOT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "<b>Step 1:</b> Use /escrow to create a new deal\n"
            "Select P2P or Product Deal type.\n\n"
            "<b>Step 2:</b> Create a private Telegram group\n"
            "Add this bot as admin to the group.\n\n"
            "<b>Step 3:</b> Link the group\n"
            "Send /link [deal_id] in the group.\n\n"
            "<b>Step 4:</b> Fill deal details\n"
            "Use /dd to enter quantity, rate, and conditions.\n\n"
            "<b>Step 5:</b> Declare roles\n"
            "Seller: /seller [wallet_address]\n"
            "Buyer: /buyer [wallet_address]\n\n"
            "<b>Step 6:</b> Select token & network\n"
            "Use /token to pick crypto and network.\n\n"
            "<b>Step 7:</b> Deposit\n"
            "Use /deposit to get the escrow address.\n"
            "Send funds within 20 minutes.\n\n"
            "<b>Step 8:</b> Complete the deal\n"
            "/release — Release funds to buyer\n"
            "/refund — Refund funds to seller\n\n"
            "⚠️ <b>Remember:</b> Once /release or /refund is used,\n"
            "payment will be sent. There is no revert!"
        ),
        parse_mode="HTML",
    )
