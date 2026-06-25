"""
Keyboard layouts for the Escrow Bot.
ReplyKeyboardMarkup and InlineKeyboardMarkup builders.
"""

from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Create the main menu ReplyKeyboardMarkup."""
    keyboard = [
        [KeyboardButton("/escrow"), KeyboardButton("/instructions")],
        [KeyboardButton("/buyer"), KeyboardButton("/seller")],
        [KeyboardButton("/deposit"), KeyboardButton("/balance")],
        [KeyboardButton("/release"), KeyboardButton("/refund")],
        [KeyboardButton("/dispute"), KeyboardButton("/save")],
        [KeyboardButton("/verify")],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def token_selection_keyboard() -> InlineKeyboardMarkup:
    """Create token selection InlineKeyboard."""
    keyboard = [
        [
            InlineKeyboardButton("LTC", callback_data="token_LTC"),
            InlineKeyboardButton("BTC", callback_data="token_BTC"),
            InlineKeyboardButton("USDT", callback_data="token_USDT"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def network_selection_keyboard(token: str) -> InlineKeyboardMarkup:
    """Create network selection InlineKeyboard based on token."""
    if token == "USDT":
        keyboard = [
            [
                InlineKeyboardButton("BSC [BEP20]", callback_data="network_BSC"),
                InlineKeyboardButton("TRON [TRC20]", callback_data="network_TRON"),
            ]
        ]
    elif token == "BTC":
        keyboard = [
            [
                InlineKeyboardButton("Bitcoin Network", callback_data="network_BTC"),
            ]
        ]
    elif token == "LTC":
        keyboard = [
            [
                InlineKeyboardButton("Litecoin Network", callback_data="network_LTC"),
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton("BSC [BEP20]", callback_data="network_BSC"),
                InlineKeyboardButton("TRON [TRC20]", callback_data="network_TRON"),
            ]
        ]
    return InlineKeyboardMarkup(keyboard)


def accept_reject_keyboard() -> InlineKeyboardMarkup:
    """Create Accept/Reject InlineKeyboard for escrow declaration."""
    keyboard = [
        [
            InlineKeyboardButton("Accept ✅", callback_data="trade_accept"),
            InlineKeyboardButton("Reject ❌", callback_data="trade_reject"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def check_payment_keyboard() -> InlineKeyboardMarkup:
    """Create Check Payment button."""
    keyboard = [
        [
            InlineKeyboardButton("🔍 Check Payment", callback_data="check_payment"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
