"""/seller and /buyer - declare roles and payout wallet addresses."""

from __future__ import annotations

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ..database import db
from ..utils import display_username, esc, is_group_chat


async def _ensure_trade(update: Update):
    chat = update.effective_chat
    trade = await db.get_trade(chat.id)
    if trade is None:
        trade = await db.create_trade(
            chat_id=chat.id, creator_id=update.effective_user.id, invite_link=""
        )
    return trade


def _role_card(role: str, username: str, user_id: int, wallet: str) -> str:
    role_label = "SELLER" if role == "seller" else "BUYER"
    return (
        "\u2554\u2550\u2550 <b>ESCROW-ROLE DECLARATION</b> \u2550\u2550\u2557\n\n"
        f"\U0001f464 <b>Role:</b> {role_label}\n"
        f"\U0001f3f7 <b>Username:</b> {esc(username)}\n"
        f"\U0001f194 <b>User ID:</b> <code>{user_id}</code>\n"
        f"\U0001f4b3 <b>Wallet:</b> <code>{esc(wallet)}</code>\n\n"
        "\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d"
    )


async def _declare(update: Update, context: ContextTypes.DEFAULT_TYPE, role: str) -> None:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if not is_group_chat(chat):
        await message.reply_text(f"Use /{role} inside the escrow group to declare your role.")
        return

    if not context.args:
        await message.reply_text(
            f"Usage: <code>/{role} &lt;WALLET_ADDRESS&gt;</code>\n"
            f"Example: <code>/{role} 0xAbc...123</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    wallet = context.args[0].strip()
    trade = await _ensure_trade(update)

    # Prevent the same person from holding both roles.
    other = "buyer" if role == "seller" else "seller"
    if trade.get(other, {}).get("user_id") == user.id:
        await message.reply_text(
            f"\u26a0\ufe0f You're already registered as the {other}. "
            "The buyer and seller must be different users."
        )
        return

    data = {
        "user_id": user.id,
        "username": user.username,
        "display": display_username(user.username, user.id),
        "wallet": wallet,
    }
    await db.set_role(chat.id, role, data)

    await message.reply_text(
        _role_card(role, data["display"], user.id, wallet),
        parse_mode=ParseMode.HTML,
    )

    # Once both roles are set, nudge toward token selection.
    refreshed = await db.get_trade(chat.id)
    if refreshed.get("seller", {}).get("wallet") and refreshed.get("buyer", {}).get("wallet"):
        await message.reply_text(
            "\u2705 Both roles declared. Use /token to choose the coin and network."
        )


async def seller_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _declare(update, context, "seller")


async def buyer_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _declare(update, context, "buyer")
