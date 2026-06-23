"""Reply and inline keyboard builders."""

from __future__ import annotations

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from .models import NETWORK_LABELS, TOKEN_NETWORKS, Network, Token


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """The persistent main-menu reply keyboard shown after /start."""
    rows = [
        [KeyboardButton("/escrow"), KeyboardButton("/instructions")],
        [KeyboardButton("/buyer"), KeyboardButton("/seller")],
        [KeyboardButton("/deposit"), KeyboardButton("/balance")],
        [KeyboardButton("/release"), KeyboardButton("/refund")],
        [KeyboardButton("/dispute"), KeyboardButton("/save"), KeyboardButton("/verify")],
    ]
    return ReplyKeyboardMarkup(
        rows, resize_keyboard=True, is_persistent=True, input_field_placeholder="Choose a command"
    )


def token_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard to choose a token (LTC / BTC / USDT)."""
    buttons = [
        InlineKeyboardButton("LTC", callback_data="token:LTC"),
        InlineKeyboardButton("BTC", callback_data="token:BTC"),
        InlineKeyboardButton("USDT", callback_data="token:USDT"),
    ]
    return InlineKeyboardMarkup([buttons])


def network_keyboard(token: Token) -> InlineKeyboardMarkup:
    """Inline keyboard to choose a network valid for the selected token."""
    row = [
        InlineKeyboardButton(NETWORK_LABELS[net], callback_data=f"network:{net.value}")
        for net in TOKEN_NETWORKS[token]
    ]
    return InlineKeyboardMarkup([row])


def accept_reject_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Accept \u2705", callback_data="declaration:accept"),
                InlineKeyboardButton("Reject \u274c", callback_data="declaration:reject"),
            ]
        ]
    )


def check_payment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Check Payment \U0001f50d", callback_data="deposit:check")]]
    )
