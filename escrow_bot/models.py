"""Domain constants and small value objects used across the bot."""

from __future__ import annotations

from enum import Enum


class TradeStatus(str, Enum):
    OPEN = "open"
    ACCEPTED = "accepted"
    DEPOSITED = "deposited"
    PAID = "paid"
    RELEASED = "released"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class Token(str, Enum):
    LTC = "LTC"
    BTC = "BTC"
    USDT = "USDT"


class Network(str, Enum):
    BEP20 = "BEP20"   # BSC
    TRC20 = "TRC20"   # TRON
    BITCOIN = "BITCOIN"
    LITECOIN = "LITECOIN"


# Which networks are valid for a given token
TOKEN_NETWORKS = {
    Token.USDT: [Network.BEP20, Network.TRC20],
    Token.BTC: [Network.BITCOIN],
    Token.LTC: [Network.LITECOIN],
}


NETWORK_LABELS = {
    Network.BEP20: "BSC [BEP20]",
    Network.TRC20: "TRON [TRC20]",
    Network.BITCOIN: "Bitcoin Network",
    Network.LITECOIN: "Litecoin Network",
}
