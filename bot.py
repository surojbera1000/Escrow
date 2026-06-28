"""
P2P Crypto Escrow Telegram Bot - Main Entry Point

A fully functional escrow bot for P2P cryptocurrency trading.
Built with python-telegram-bot v20+ (async).

Usage:
    1. Set BOT_TOKEN in .env file or environment variable
    2. Run: python bot.py
"""
import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, BOT_NAME, BOT_VERSION
from handlers.start import start_command, start_button_callback, instructions_command
from handlers.escrow import escrow_command, escrow_type_callback, link_command, on_bot_added_to_group
from handlers.deal import dd_conversation_handler
from handlers.roles import seller_command, buyer_command
from handlers.token import token_command, token_callback, network_callback, deal_accept_callback, deal_reject_callback
from handlers.deposit import deposit_command, check_payment_callback
from handlers.release_refund import release_command, refund_command, confirm_action_callback
from handlers.dispute import dispute_command, dispute_callback, balance_command, save_command, verify_command

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def help_command(update: Update, context) -> None:
    """Handle /help command."""
    await update.message.reply_text(
        text=(
            "📖 <b>HELP - P2P CRYPTO ESCROW BOT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "<b>🔹 Getting Started:</b>\n"
            "/start — Show main menu\n"
            "/escrow — Create a new escrow deal\n"
            "/link [deal_id] — Link group to a deal\n\n"
            "<b>🔹 Deal Setup (in group):</b>\n"
            "/dd — Fill deal details (quantity, rate, conditions)\n"
            "/seller [wallet] — Register as seller\n"
            "/buyer [wallet] — Register as buyer\n"
            "/token — Select cryptocurrency & network\n\n"
            "<b>🔹 Transaction:</b>\n"
            "/deposit — Generate deposit address\n"
            "/balance — Check escrow balance\n"
            "/verify — Verify transaction status\n\n"
            "<b>🔹 Completion:</b>\n"
            "/release — Release funds to buyer\n"
            "/refund — Refund funds to seller\n\n"
            "<b>🔹 Other:</b>\n"
            "/dispute — Open a dispute\n"
            "/save — Save deal data\n"
            "/cancel — Cancel current operation\n"
            "/help — Show this help message\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 {BOT_NAME} v{BOT_VERSION}"
        ),
        parse_mode="HTML",
    )


async def error_handler(update: object, context) -> None:
    """Handle errors in the bot."""
    logger.error(f"Exception while handling an update: {context.error}")
    
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ An error occurred while processing your request.\n"
                "Please try again or contact support."
            )
        except Exception:
            pass


def main() -> None:
    """Initialize and start the bot."""
    # Validate token
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("=" * 50)
        print("ERROR: Bot token not configured!")
        print("")
        print("Please set your bot token:")
        print("  1. Copy .env.example to .env")
        print("  2. Replace 'your_telegram_bot_token_here' with your actual token")
        print("  3. Get a token from @BotFather on Telegram")
        print("=" * 50)
        sys.exit(1)
    
    print(f"🚀 Starting {BOT_NAME} v{BOT_VERSION}...")
    
    # Build the application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # ─── Command Handlers ───────────────────────────────────────
    
    # Start & Help
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("instructions", instructions_command))
    
    # Escrow creation & linking
    application.add_handler(CommandHandler("escrow", escrow_command))
    application.add_handler(CommandHandler("link", link_command))
    
    # Deal details (ConversationHandler - must be added before generic handlers)
    application.add_handler(dd_conversation_handler)
    
    # Role declaration
    application.add_handler(CommandHandler("seller", seller_command))
    application.add_handler(CommandHandler("buyer", buyer_command))
    
    # Token selection
    application.add_handler(CommandHandler("token", token_command))
    
    # Deposit
    application.add_handler(CommandHandler("deposit", deposit_command))
    
    # Release & Refund
    application.add_handler(CommandHandler("release", release_command))
    application.add_handler(CommandHandler("refund", refund_command))
    
    # Utility commands
    application.add_handler(CommandHandler("dispute", dispute_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("save", save_command))
    application.add_handler(CommandHandler("verify", verify_command))
    
    # ─── Callback Query Handlers ────────────────────────────────
    
    # Start button
    application.add_handler(CallbackQueryHandler(start_button_callback, pattern="^start_menu$"))
    
    # Escrow type selection
    application.add_handler(CallbackQueryHandler(escrow_type_callback, pattern="^escrow_type_"))
    
    # Token selection
    application.add_handler(CallbackQueryHandler(token_callback, pattern="^token_"))
    
    # Network selection
    application.add_handler(CallbackQueryHandler(network_callback, pattern="^network_"))
    
    # Deal accept/reject
    application.add_handler(CallbackQueryHandler(deal_accept_callback, pattern="^deal_accept$"))
    application.add_handler(CallbackQueryHandler(deal_reject_callback, pattern="^deal_reject$"))
    
    # Check payment
    application.add_handler(CallbackQueryHandler(check_payment_callback, pattern="^check_payment$"))
    
    # Release/Refund confirmation
    application.add_handler(CallbackQueryHandler(confirm_action_callback, pattern="^confirm_release_"))
    application.add_handler(CallbackQueryHandler(confirm_action_callback, pattern="^confirm_refund_"))
    
    # Dispute callbacks
    application.add_handler(CallbackQueryHandler(dispute_callback, pattern="^dispute_"))
    
    # ─── Message Handlers ───────────────────────────────────────
    
    # Handle bot being added to a group
    application.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            on_bot_added_to_group,
        )
    )
    
    # ─── Error Handler ──────────────────────────────────────────
    application.add_error_handler(error_handler)
    
    # ─── Start the bot ──────────────────────────────────────────
    print("✅ Bot is running! Press Ctrl+C to stop.")
    print(f"📋 Registered commands: /start, /help, /escrow, /link, /dd, /seller, /buyer,")
    print(f"   /token, /deposit, /release, /refund, /dispute, /balance, /save, /verify")
    
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
