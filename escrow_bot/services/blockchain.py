"""Blockchain balance / payment checking for each supported network.

The bot polls the deposit address and reports how much has arrived so far.

- BEP20 (BSC)  : web3.py reads the BEP20 USDT contract balance, or native BNB.
- TRC20 (TRON) : tronpy reads the TRC20 USDT contract balance, or native TRX.
- BTC / LTC    : a public block-explorer REST API (BlockCypher) reports balance.

All functions return the **total amount currently held by the address** in human
units (float). The handler compares this against the expected trade amount.
"""

from __future__ import annotations

import asyncio
from typing import Optional

import aiohttp

from ..config import settings
from ..models import Network, Token

# Standard minimal ABI fragments for an ERC20/BEP20 token
_ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
]


# --------------------------------------------------------------------------- BEP20
def _check_bep20_sync(address: str, token: Token) -> float:
    from web3 import Web3

    w3 = Web3(Web3.HTTPProvider(settings.bsc_rpc_url))
    checksum = Web3.to_checksum_address(address)

    if token == Token.USDT:
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(settings.usdt_bep20_contract),
            abi=_ERC20_ABI,
        )
        decimals = contract.functions.decimals().call()
        raw = contract.functions.balanceOf(checksum).call()
        return raw / (10 ** decimals)

    # Native BNB balance fallback
    raw = w3.eth.get_balance(checksum)
    return raw / (10 ** 18)


# --------------------------------------------------------------------------- TRC20
def _check_trc20_sync(address: str, token: Token) -> float:
    from tronpy import Tron
    from tronpy.providers import HTTPProvider

    if settings.tron_api_key:
        provider = HTTPProvider(api_key=settings.tron_api_key)
        client = Tron(provider=provider)
    else:
        client = Tron(network=settings.tron_network)

    if token == Token.USDT:
        contract = client.get_contract(settings.usdt_trc20_contract)
        decimals = contract.functions.decimals()
        raw = contract.functions.balanceOf(address)
        return raw / (10 ** decimals)

    # Native TRX balance fallback
    return float(client.get_account_balance(address))


# ------------------------------------------------------------------ BTC / LTC
async def _check_blockcypher(address: str, coin: str) -> float:
    """coin is 'btc' or 'ltc'. Returns confirmed+unconfirmed balance in coin units."""
    url = f"https://api.blockcypher.com/v1/{coin}/main/addrs/{address}/balance"
    params = {}
    if settings.blockcypher_token:
        params["token"] = settings.blockcypher_token
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            resp.raise_for_status()
            data = await resp.json()
    # BlockCypher returns satoshis (1e8 base units) for both BTC and LTC
    total = data.get("final_balance", data.get("balance", 0))
    return total / (10 ** 8)


# ------------------------------------------------------------------- dispatch
async def get_received_amount(address: str, token: Token, network: Network) -> float:
    """Return the total amount currently held by ``address`` in human units."""
    if network == Network.BEP20:
        return await asyncio.to_thread(_check_bep20_sync, address, token)
    if network == Network.TRC20:
        return await asyncio.to_thread(_check_trc20_sync, address, token)
    if network == Network.BITCOIN:
        return await _check_blockcypher(address, "btc")
    if network == Network.LITECOIN:
        return await _check_blockcypher(address, "ltc")
    raise ValueError(f"Unsupported network: {network}")


async def safe_get_received_amount(
    address: str, token: Token, network: Network
) -> Optional[float]:
    """Like ``get_received_amount`` but returns None instead of raising on error."""
    try:
        return await get_received_amount(address, token, network)
    except Exception:  # noqa: BLE001 - network/RPC errors are expected sometimes
        return None
