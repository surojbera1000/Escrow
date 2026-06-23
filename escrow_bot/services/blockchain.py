"""Blockchain balance checking.

This build only supports **USDT on BSC (BEP20)**. The balance is read with a
plain JSON-RPC ``eth_call`` to the token contract's ``balanceOf`` method over
``httpx`` - no heavy SDK (web3 / tronpy) and therefore no native build step at
deploy time.

Other networks (TRON / Bitcoin / Litecoin) are intentionally unsupported here:
``get_received_amount`` returns ``None`` for them so the rest of the bot can
show them in menus while making clear they don't process deposits yet.
"""

from __future__ import annotations

from typing import Optional

import httpx

from ..config import settings
from ..models import Network, Token

# keccak256("balanceOf(address)")[:4]
_BALANCE_OF_SELECTOR = "0x70a08231"
# USDT on BSC uses 18 decimals
_USDT_BEP20_DECIMALS = 18


async def _bep20_usdt_balance(address: str) -> float:
    """Read the USDT BEP20 balance of ``address`` via JSON-RPC eth_call."""
    addr_hex = address.lower().removeprefix("0x").rjust(64, "0")
    data = _BALANCE_OF_SELECTOR + addr_hex

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_call",
        "params": [{"to": settings.usdt_bep20_contract, "data": data}, "latest"],
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(settings.bsc_rpc_url, json=payload)
        resp.raise_for_status()
        body = resp.json()

    if "error" in body:
        raise RuntimeError(f"RPC error: {body['error']}")

    result = body.get("result", "0x0")
    raw = int(result, 16) if result not in (None, "0x", "") else 0
    return raw / (10 ** _USDT_BEP20_DECIMALS)


async def get_received_amount(address: str, token: Token, network: Network) -> Optional[float]:
    """Total amount held by ``address`` in human units, or None if unsupported."""
    if network == Network.BEP20 and token == Token.USDT:
        return await _bep20_usdt_balance(address)
    # All other token/network combinations are not active in this build.
    return None


async def safe_get_received_amount(
    address: str, token: Token, network: Network
) -> Optional[float]:
    """Like ``get_received_amount`` but returns None instead of raising on error."""
    try:
        return await get_received_amount(address, token, network)
    except Exception:  # noqa: BLE001 - network/RPC errors are expected sometimes
        return None
