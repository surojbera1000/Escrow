"""
Main entry point for the Telegram Escrow Bot.
Registers all handlers and starts the bot.
"""

import logging
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
)

from config.settings import BOT_TOKEN
from models.database import MongoDB
from handlers.start import (
    start_command,
    instructions_command,
    balance_command,
    save_command,
    verify_command,
)
from handlers.escrow import escrow_command
from handlers.deal import get_deal_conversation_handler
from handlers.roles import seller_command, buyer_command
from handlers.token import token_command, token_callback, network_callback
from handlers.trade import (
    trade_accept_callback,
    trade_reject_callback,
    deposit_command,
    check_payment_callback,
)
from handlers.release import release_command, refund_command, dispute_command
from services.payment_monitor import setup_payment_monitor

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Initialize and run the bot."""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set! Please configure .env file.")
        return

    # Connect to MongoDB
    logger.info("Connecting to MongoDB...")
    MongoDB.connect()
    logger.info("MongoDB connected successfully.")


    # Build application
    application = Application.builder().token(BOT_TOKEN).build()

    # ─── Register Command Handlers ────────────────────────────────────────────
    # Basic commands (private chat)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("instructions", instructions_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("save", save_command))
    application.add_handler(CommandHandler("verify", verify_command))

    # Escrow group creation (private chat)
    application.add_handler(CommandHandler("escrow", escrow_command))

    # Deal info conversation handler (group)
    application.add_handler(get_deal_conversation_handler())

    # Role assignment (group)
    application.add_handler(CommandHandler("seller", seller_command))
    application.add_handler(CommandHandler("buyer", buyer_command))

    # Token/network selection (group)
    application.add_handler(CommandHandler("token", token_command))

    # Deposit (group)
    application.add_handler(CommandHandler("deposit", deposit_command))

    # Release/Refund/Dispute (group)
    application.add_handler(CommandHandler("release", release_command))
    application.add_handler(CommandHandler("refund", refund_command))
    application.add_handler(CommandHandler("dispute", dispute_command))

    # ─── Register Callback Query Handlers ─────────────────────────────────────
    application.add_handler(CallbackQueryHandler(token_callback, pattern="^token_"))
    application.add_handler(CallbackQueryHandler(network_callback, pattern="^network_"))
    application.add_handler(CallbackQueryHandler(trade_accept_callback, pattern="^trade_accept$"))
    application.add_handler(CallbackQueryHandler(trade_reject_callback, pattern="^trade_reject$"))
    application.add_handler(CallbackQueryHandler(check_payment_callback, pattern="^check_payment$"))

    # ─── Setup Background Jobs ────────────────────────────────────────────────
    setup_payment_monitor(application)

    # ─── Start the Bot ────────────────────────────────────────────────────────
    logger.info("🤖 Escrow Bot starting...")
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
