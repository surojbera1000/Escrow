"""
Background payment monitoring service.
Polls deposit addresses every 60 seconds to detect incoming payments.
"""

import asyncio
import logging
from datetime import datetime

from telegram.ext import ContextTypes

from models.trade import TradeModel, TradeStatus
from models.database import MongoDB
from services.blockchain import payment_verifier
from config.settings import PAYMENT_CHECK_INTERVAL_SECONDS

logger = logging.getLogger(__name__)


async def payment_monitor_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Background job that checks all pending deposits.
    Runs every PAYMENT_CHECK_INTERVAL_SECONDS.
    """
    try:
        db = MongoDB.get_db()

        # Find all trades waiting for deposits
        pending_trades = db.trades.find(
            {"status": TradeStatus.DEPOSIT_PENDING, "deposit_address": {"$ne": None}}
        )

        for trade in pending_trades:
            group_id = trade["group_id"]
            address = trade["deposit_address"]
            network = trade.get("network", "BSC")
            token = trade.get("token", "USDT")

            try:
                # Check for payments
                amount = await payment_verifier.check_payment(network, address)

                if amount > 0 and amount != trade.get("amount_received", 0):
                    # Payment detected! Update the database
                    TradeModel.update_amount_received(group_id, amount)

                    # Notify the group
                    await context.bot.send_message(
                        chat_id=group_id,
                        text=(
                            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            "✅ <b>PAYMENT DETECTED</b>\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                            f"💵 <b>Amount Received:</b> {amount:.5f} {token}\n\n"
                            "Funds are now held in escrow. ✅\n"
                            "Seller can use /release to complete the trade.\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                        ),
                        parse_mode="HTML",
                    )
                    logger.info(
                        f"Payment detected for group {group_id}: {amount} {token}"
                    )

            except Exception as e:
                logger.error(f"Error checking payment for group {group_id}: {e}")

    except Exception as e:
        logger.error(f"Payment monitor error: {e}")


def setup_payment_monitor(application) -> None:
    """Set up the recurring payment monitor job."""
    job_queue = application.job_queue
    job_queue.run_repeating(
        payment_monitor_job,
        interval=PAYMENT_CHECK_INTERVAL_SECONDS,
        first=30,  # Start after 30 seconds
        name="payment_monitor",
    )
    logger.info(
        f"Payment monitor started (interval: {PAYMENT_CHECK_INTERVAL_SECONDS}s)"
    )
