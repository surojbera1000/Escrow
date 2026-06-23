"""Application entry point - wires handlers, DB and the userbot together."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
)

from .config import settings
from .database import db
from .handlers import deposit, misc, roles, settlement, start, token
from .handlers.deal import build_deal_conversation
from .handlers.escrow import escrow_command
from .services.group_manager import group_manager

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def _post_init(app: Application) -> None:
    """Connect external services once the event loop is running."""
    await db.connect()
    await group_manager.start()
    logger.info("Database connected. Group manager available=%s", group_manager.available)


async def _post_shutdown(app: Application) -> None:
    await group_manager.stop()
    await db.close()
    logger.info("Shutdown complete.")


def build_application() -> Application:
    settings.validate()

    app = (
        ApplicationBuilder()
        .token(settings.bot_token)
        .post_init(_post_init)
        .post_shutdown(_post_shutdown)
        .build()
    )

    # --- core / menu ---
    app.add_handler(CommandHandler("start", start.start_command))
    app.add_handler(CommandHandler("instructions", start.instructions_command))
    app.add_handler(CommandHandler("escrow", escrow_command))

    # --- deal info form (conversation) ---
    app.add_handler(build_deal_conversation())

    # --- roles ---
    app.add_handler(CommandHandler("seller", roles.seller_command))
    app.add_handler(CommandHandler("buyer", roles.buyer_command))

    # --- token / network selection ---
    app.add_handler(CommandHandler("token", token.token_command))
    app.add_handler(CallbackQueryHandler(token.token_chosen, pattern=r"^token:"))
    app.add_handler(CallbackQueryHandler(token.network_chosen, pattern=r"^network:"))
    app.add_handler(CallbackQueryHandler(token.declaration_response, pattern=r"^declaration:"))

    # --- deposit / balance / payment checks ---
    app.add_handler(CommandHandler("deposit", deposit.deposit_command))
    app.add_handler(CommandHandler("balance", deposit.balance_command))
    app.add_handler(CallbackQueryHandler(deposit.check_payment_callback, pattern=r"^deposit:check$"))

    # --- settlement ---
    app.add_handler(CommandHandler("release", settlement.release_command))
    app.add_handler(CommandHandler("refund", settlement.refund_command))
    app.add_handler(CommandHandler("dispute", settlement.dispute_command))

    # --- misc menu commands ---
    app.add_handler(CommandHandler("save", misc.save_command))
    app.add_handler(CommandHandler("verify", misc.verify_command))

    return app


def main() -> None:
    app = build_application()
    logger.info("Starting Escrow Bot...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
