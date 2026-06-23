"""/save and /verify menu commands."""

from __future__ import annotations

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ..database import db
from ..models import NETWORK_LABELS, Network
from ..utils import esc, fmt_time, is_group_chat, short_addr


async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Save / print a full summary of the current deal for the records."""
    chat = update.effective_chat
    message = update.effective_message
    if not is_group_chat(chat):
        await message.reply_text("Use /save inside the escrow group.")
        return

    trade = await db.get_trade(chat.id)
    if not trade:
        await message.reply_text("No active trade to save.")
        return

    deal = trade.get("deal", {})
    seller = trade.get("seller", {})
    buyer = trade.get("buyer", {})
    network = trade.get("network")
    network_label = NETWORK_LABELS.get(Network(network), network) if network else "-"

    text = (
        "\U0001f4be <b>DEAL SUMMARY (SAVED)</b>\n\n"
        f"\U0001f7e2 <b>Status:</b> {esc(trade.get('status'))}\n"
        f"\U0001f4e6 <b>Quantity:</b> {esc(deal.get('quantity', '-'))}\n"
        f"\U0001f4b1 <b>Rate:</b> {esc(deal.get('rate', '-'))}\n"
        f"\U0001f4cb <b>Conditions:</b> {esc(deal.get('conditions', '-'))}\n\n"
        f"\U0001f9d1\u200d\U0001f4bc <b>Seller:</b> {esc(seller.get('display', '-'))} \u2192 "
        f"<code>{esc(seller.get('wallet', '-'))}</code>\n"
        f"\U0001f6cd <b>Buyer:</b> {esc(buyer.get('display', '-'))} \u2192 "
        f"<code>{esc(buyer.get('wallet', '-'))}</code>\n\n"
        f"\U0001fa99 <b>Token:</b> {esc(trade.get('token', '-'))}\n"
        f"\U0001f310 <b>Network:</b> {esc(network_label)}\n"
        f"\U0001f4cd <b>Escrow Address:</b> <code>{esc(trade.get('deposit', {}).get('address', '-'))}</code>\n"
        f"\U0001f552 <b>Created:</b> {fmt_time(trade.get('created_at'))}"
    )
    await message.reply_text(text, parse_mode=ParseMode.HTML)


async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show a quick verification of the deal's readiness/integrity."""
    chat = update.effective_chat
    message = update.effective_message
    if not is_group_chat(chat):
        await message.reply_text("Use /verify inside the escrow group.")
        return

    trade = await db.get_trade(chat.id)
    if not trade:
        await message.reply_text("No active trade to verify.")
        return

    checks = [
        ("Deal info filled (/dd)", bool(trade.get("deal"))),
        ("Seller declared", bool(trade.get("seller", {}).get("wallet"))),
        ("Buyer declared", bool(trade.get("buyer", {}).get("wallet"))),
        ("Token & network selected", bool(trade.get("token") and trade.get("network"))),
        ("Deposit address generated", bool(trade.get("deposit", {}).get("address"))),
    ]
    tick, cross = "\u2705", "\u274c"
    lines = [f"{tick if ok else cross} {label}" for label, ok in checks]
    addr = trade.get("deposit", {}).get("address")
    body = "\n".join(lines)
    text = (
        "\U0001f50e <b>TRADE VERIFICATION</b>\n\n"
        f"{body}\n\n"
        f"Escrow address: <code>{esc(short_addr(addr))}</code>"
    )
    await message.reply_text(text, parse_mode=ParseMode.HTML)
