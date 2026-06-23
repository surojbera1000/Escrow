"""/token - choose coin + network, then show the ESCROW DECLARATION card."""

from __future__ import annotations

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ..database import db
from ..keyboards import accept_reject_keyboard, network_keyboard, token_keyboard
from ..models import NETWORK_LABELS, Network, Token, TradeStatus
from ..utils import esc, fmt_time, is_group_chat, now_utc


async def token_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.effective_message

    if not is_group_chat(chat):
        await message.reply_text("Use /token inside the escrow group.")
        return

    trade = await db.get_trade(chat.id)
    if not trade or not trade.get("seller", {}).get("wallet") or not trade.get("buyer", {}).get("wallet"):
        await message.reply_text(
            "\u26a0\ufe0f Both /seller and /buyer must declare their wallets before selecting a token."
        )
        return

    await message.reply_text(
        "\U0001fa99 <b>Select the token for this trade:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=token_keyboard(),
    )


async def token_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    token = Token(query.data.split(":", 1)[1])

    await db.update_trade(query.message.chat.id, {"token": token.value, "network": None})

    await query.edit_message_text(
        f"\U0001fa99 Token selected: <b>{token.value}</b>\n\nNow choose the network:",
        parse_mode=ParseMode.HTML,
        reply_markup=network_keyboard(token),
    )


async def network_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    network = Network(query.data.split(":", 1)[1])
    chat_id = query.message.chat.id

    trade = await db.get_trade(chat_id)
    if not trade:
        await query.edit_message_text("Trade not found. Please restart with /token.")
        return

    await db.update_trade(chat_id, {"network": network.value})
    trade["network"] = network.value

    token = trade.get("token")
    buyer = trade.get("buyer", {})
    seller = trade.get("seller", {})

    card = (
        "\u2554\u2550\u2550 <b>ESCROW DECLARATION</b> \u2550\u2550\u2557\n\n"
        f"\U0001f9d1\u200d\U0001f4bc <b>Seller:</b> {esc(seller.get('display', '-'))}\n"
        f"\U0001f6cd <b>Buyer:</b> {esc(buyer.get('display', '-'))}\n"
        f"\U0001f194 <b>Buyer UserID:</b> <code>{esc(buyer.get('user_id'))}</code>\n"
        f"\U0001fa99 <b>Crypto:</b> {esc(token)}\n"
        f"\U0001f310 <b>Network:</b> {esc(NETWORK_LABELS.get(network, network.value))}\n\n"
        "Both parties, please confirm to proceed.\n"
        "\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d"
    )
    await query.edit_message_text(
        card, parse_mode=ParseMode.HTML, reply_markup=accept_reject_keyboard()
    )


async def declaration_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    decision = query.data.split(":", 1)[1]
    chat_id = query.message.chat.id
    user = query.from_user

    trade = await db.get_trade(chat_id)
    if not trade:
        await query.answer("Trade not found.", show_alert=True)
        return

    # Only the buyer or seller may accept/reject.
    participant_ids = {
        trade.get("seller", {}).get("user_id"),
        trade.get("buyer", {}).get("user_id"),
    }
    if user.id not in participant_ids:
        await query.answer("Only the buyer or seller can respond.", show_alert=True)
        return

    if decision == "reject":
        await query.answer()
        await db.set_status(chat_id, TradeStatus.OPEN.value)
        await query.edit_message_text(
            "\u274c <b>Escrow declaration rejected.</b>\nRe-run /token to start over.",
            parse_mode=ParseMode.HTML,
        )
        return

    # Accept flow - track which parties have accepted.
    accepted = set(trade.get("accepted_by", []))
    accepted.add(user.id)
    await db.update_trade(chat_id, {"accepted_by": list(accepted)})

    if participant_ids.issubset(accepted):
        await query.answer("Accepted!")
        await db.set_status(chat_id, TradeStatus.ACCEPTED.value)
        await _post_transaction_info(update, context, chat_id)
    else:
        await query.answer("Your acceptance is recorded. Waiting for the other party.")
        await query.edit_message_reply_markup(reply_markup=accept_reject_keyboard())


async def _post_transaction_info(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    trade = await db.get_trade(chat_id)
    seller = trade.get("seller", {})
    buyer = trade.get("buyer", {})
    network = trade.get("network")
    network_label = NETWORK_LABELS.get(Network(network), network) if network else "-"

    text = (
        "\U0001f4dc <b>TRANSACTION INFORMATION</b>\n\n"
        f"\U0001f9d1\u200d\U0001f4bc <b>Seller:</b> {esc(seller.get('display', '-'))}\n"
        f"\U0001f6cd <b>Buyer:</b> {esc(buyer.get('display', '-'))}\n"
        f"\U0001fa99 <b>Token:</b> {esc(trade.get('token'))}\n"
        f"\U0001f310 <b>Network:</b> {esc(network_label)}\n"
        f"\U0001f552 <b>Start Time:</b> {fmt_time(now_utc())}\n\n"
        "\u2757\ufe0f <b>IMPORTANT</b>\n"
        "Make sure to finalise and agree each-others terms before depositing. "
        "Please use the /deposit command to generate a deposit address for your trade."
    )
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)

    # Bonus: swap the group photo now that the trade has started.
    from .group_photo import set_trade_group_photo

    await set_trade_group_photo(context, chat_id)
