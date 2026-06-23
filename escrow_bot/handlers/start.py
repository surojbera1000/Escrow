"""/start, /instructions and the main menu."""

from __future__ import annotations

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ..database import db
from ..keyboards import main_menu_keyboard

WELCOME_TEXT = (
    "\U0001f6e1 <b>Welcome to the Escrow Bot</b>\n\n"
    "I provide a secure peer-to-peer (P2P) escrow service for "
    "<b>USDT, BTC and LTC</b> trades.\n\n"
    "Use the menu below to get started:\n"
    "\u2022 /escrow \u2013 create a new private escrow group\n"
    "\u2022 /instructions \u2013 how the escrow process works\n"
    "\u2022 /buyer / /seller \u2013 declare your role &amp; wallet\n"
    "\u2022 /deposit \u2013 generate the escrow deposit address\n"
    "\u2022 /balance \u2013 check funds received\n"
    "\u2022 /release / /refund \u2013 settle the trade (seller only)\n"
    "\u2022 /dispute \u2013 raise a dispute for moderator review"
)

INSTRUCTIONS_TEXT = (
    "\U0001f4d6 <b>How the Escrow Works</b>\n\n"
    "<b>1.</b> A trader sends /escrow to me in private. I create a fresh private "
    "group and send back an invite link.\n"
    "<b>2.</b> The buyer and seller both join the group.\n"
    "<b>3.</b> Inside the group run /dd and fill the Deal Info Form "
    "(Quantity, Rate, Conditions).\n"
    "<b>4.</b> The seller runs <code>/seller &lt;wallet&gt;</code> and the buyer runs "
    "<code>/buyer &lt;wallet&gt;</code> to declare roles and payout wallets.\n"
    "<b>5.</b> Use /token to choose the coin and network, then both parties "
    "<b>Accept</b> the escrow declaration.\n"
    "<b>6.</b> Use /deposit to generate a unique escrow address. The buyer sends "
    "the agreed amount there.\n"
    "<b>7.</b> I monitor the blockchain and confirm when the funds arrive.\n"
    "<b>8.</b> After the buyer receives the goods/service, the <b>seller</b> runs "
    "/release to send funds to the buyer, or /refund to return them.\n\n"
    "\u26a0\ufe0f Only the assigned <b>seller</b> can /release or /refund. "
    "Never trade outside the escrow group."
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user:
        await db.upsert_user(user.id, user.username, user.first_name)
    await update.effective_message.reply_text(
        WELCOME_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(),
    )


async def instructions_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        INSTRUCTIONS_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(),
    )
