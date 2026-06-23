"""/deposit + /balance + payment monitoring.

This build processes deposits for **USDT on BSC (BEP20) only**, using a single
fixed escrow receiving address (``BEP20_DEPOSIT_ADDRESS``). Because that address
is shared across trades, we record the address balance at the moment /deposit is
run (a "baseline") and report the *increase* since then as this trade's payment.

A repeating job polls the chain every ``poll_interval_seconds`` and updates the
deposit message when funds arrive. Other networks are shown in menus but reply
that they're not supported yet.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ..config import settings
from ..database import db
from ..keyboards import check_payment_keyboard
from ..models import NETWORK_LABELS, Network, Token, TradeStatus
from ..services import blockchain
from ..utils import esc, is_group_chat, now_utc

logger = logging.getLogger(__name__)


def _usd_estimate(amount: float, token: str) -> str:
    # USDT is pegged ~1:1 to USD.
    if token == Token.USDT.value:
        return f"{amount:.5f} [{amount:.2f}$]"
    return f"{amount:.8f}"


def _is_supported(trade: dict) -> bool:
    return trade.get("network") == Network.BEP20.value and trade.get("token") == Token.USDT.value


def _deposit_text(trade: dict, address: str, expires_at, received: float = 0.0) -> str:
    network = trade.get("network")
    network_label = NETWORK_LABELS.get(Network(network), network) if network else "-"
    token = trade.get("token", "-")
    minutes_left = max(0.0, (expires_at - now_utc()).total_seconds() / 60.0)

    return (
        "\U0001f4b0 <b>ESCROW DEPOSIT ADDRESS</b>\n\n"
        f"\U0001fa99 <b>Token:</b> {esc(token)}\n"
        f"\U0001f310 <b>Network:</b> {esc(network_label)}\n\n"
        f"\U0001f4cd <b>Deposit Address:</b>\n<code>{esc(address)}</code>\n\n"
        f"\u23f3 <b>Address Reset Timer:</b> {minutes_left:.2f} minutes\n"
        f"\U0001f4b5 <b>Amount Received:</b> {_usd_estimate(received, token)}\n\n"
        "Send the agreed amount to the address above. I check the blockchain "
        "automatically, or press the button below to check now."
    )


async def deposit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.effective_message

    if not is_group_chat(chat):
        await message.reply_text("Use /deposit inside the escrow group.")
        return

    trade = await db.get_trade(chat.id)
    if not trade or not trade.get("token") or not trade.get("network"):
        await message.reply_text(
            "\u26a0\ufe0f Select a token and network first with /token, then accept the declaration."
        )
        return

    if trade.get("status") not in (TradeStatus.ACCEPTED.value, TradeStatus.DEPOSITED.value):
        await message.reply_text(
            "\u26a0\ufe0f Both parties must Accept the escrow declaration before depositing."
        )
        return

    # Only USDT on BSC [BEP20] is active in this build.
    if not _is_supported(trade):
        await message.reply_text(
            "\u26a0\ufe0f <b>Not available yet.</b>\n\n"
            "This escrow currently processes deposits only for <b>USDT</b> on "
            "<b>BSC [BEP20]</b>.\n\n"
            "Please run /token, choose <b>USDT</b>, then select <b>BSC[BEP20]</b>.",
            parse_mode=ParseMode.HTML,
        )
        return

    address = settings.bep20_deposit_address

    existing = trade.get("deposit", {})
    if existing.get("address") == address and existing.get("expires_at") and existing["expires_at"] > now_utc():
        # Reuse the active deposit session for this trade.
        expires_at = existing["expires_at"]
        received = existing.get("amount_received", 0.0)
    else:
        # New deposit session: snapshot the current address balance as a baseline
        # so we can attribute the *increase* to this trade.
        baseline = await blockchain.safe_get_received_amount(address, Token.USDT, Network.BEP20)
        if baseline is None:
            baseline = 0.0
        expires_at = now_utc() + timedelta(minutes=settings.deposit_ttl_minutes)
        received = 0.0
        await db.update_trade(
            chat.id,
            {
                "deposit": {
                    "address": address,
                    "baseline": baseline,
                    "expires_at": expires_at,
                    "amount_received": 0.0,
                },
                "status": TradeStatus.DEPOSITED.value,
            },
        )
        trade = await db.get_trade(chat.id)

    sent = await message.reply_text(
        _deposit_text(trade, address, expires_at, received),
        parse_mode=ParseMode.HTML,
        reply_markup=check_payment_keyboard(),
    )

    await db.update_trade(chat.id, {"deposit.message_id": sent.message_id})
    _schedule_payment_job(context, chat.id)


def _schedule_payment_job(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    job_queue = getattr(context, "job_queue", None)
    if job_queue is None:
        return
    name = f"poll:{chat_id}"
    for job in job_queue.get_jobs_by_name(name):
        job.schedule_removal()
    job_queue.run_repeating(
        poll_payment_job,
        interval=settings.poll_interval_seconds,
        first=settings.poll_interval_seconds,
        name=name,
        chat_id=chat_id,
        data={"chat_id": chat_id},
    )


async def _refresh_payment(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Query the chain and update the trade + deposit message. Returns received amount."""
    trade = await db.get_trade(chat_id)
    if not trade:
        return None
    deposit = trade.get("deposit", {})
    address = deposit.get("address")
    if not address or not _is_supported(trade):
        return None

    current = await blockchain.safe_get_received_amount(address, Token.USDT, Network.BEP20)
    if current is None:
        return None

    baseline = deposit.get("baseline", 0.0)
    received = max(0.0, current - baseline)
    await db.update_trade(chat_id, {"deposit.amount_received": received})

    message_id = deposit.get("message_id")
    if message_id:
        expires_at = deposit.get("expires_at") or now_utc()
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=_deposit_text(trade, address, expires_at, received),
                parse_mode=ParseMode.HTML,
                reply_markup=check_payment_keyboard(),
            )
        except Exception:  # noqa: BLE001 - "message is not modified" etc.
            pass

    return received


async def poll_payment_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.data["chat_id"]
    trade = await db.get_trade(chat_id)
    if not trade:
        context.job.schedule_removal()
        return

    if trade.get("status") not in (TradeStatus.DEPOSITED.value,):
        context.job.schedule_removal()
        return

    received = await _refresh_payment(context, chat_id)
    if received is None:
        return

    expected = trade.get("deposit", {}).get("amount_expected")
    if received and (expected is None or received + 1e-9 >= expected):
        await db.set_status(chat_id, TradeStatus.PAID.value)
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "\u2705 <b>Payment detected!</b>\n"
                f"Amount received: <b>{received:.5f}</b> {esc(trade.get('token'))}.\n\n"
                "Buyer, please confirm delivery. The <b>seller</b> can now use "
                "/release to send funds to the buyer or /refund to return them."
            ),
            parse_mode=ParseMode.HTML,
        )
        context.job.schedule_removal()


async def check_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("Checking the blockchain...")
    received = await _refresh_payment(context, query.message.chat.id)
    if received is None:
        await query.answer("Could not reach the network right now. Try again shortly.", show_alert=True)


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.effective_message
    if not is_group_chat(chat):
        await message.reply_text("Use /balance inside the escrow group.")
        return

    trade = await db.get_trade(chat.id)
    if not trade or not trade.get("deposit", {}).get("address"):
        await message.reply_text("No deposit address yet. Use /deposit first.")
        return

    received = await _refresh_payment(context, chat.id)
    if received is None:
        received = trade.get("deposit", {}).get("amount_received", 0.0)

    await message.reply_text(
        f"\U0001f4b5 <b>Amount Received:</b> {_usd_estimate(received, trade.get('token', '-'))}",
        parse_mode=ParseMode.HTML,
    )
