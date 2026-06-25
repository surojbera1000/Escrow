"""
Blockchain integration service.
Handles payment verification for BSC (BEP20) and TRON (TRC20) networks.
Uses web3.py for BSC and tronpy for TRC20.
"""

import asyncio
import logging
from typing import Optional
from decimal import Decimal

from config.settings import (
    BSC_RPC_URL,
    TRON_RPC_URL,
    TRON_API_KEY,
    BSC_USDT_CONTRACT,
    TRON_USDT_CONTRACT,
    ESCROW_BSC_ADDRESS,
    ESCROW_TRON_ADDRESS,
    PAYMENT_CHECK_INTERVAL_SECONDS,
)

logger = logging.getLogger(__name__)

# ERC20/BEP20 Transfer event ABI (minimal)
ERC20_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    },
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



class BSCChecker:
    """BSC/BEP20 payment verification using web3.py."""

    def __init__(self):
        self._web3 = None
        self._contract = None

    @property
    def web3(self):
        if self._web3 is None:
            from web3 import Web3
            self._web3 = Web3(Web3.HTTPProvider(BSC_RPC_URL))
        return self._web3

    @property
    def usdt_contract(self):
        if self._contract is None:
            self._contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address(BSC_USDT_CONTRACT),
                abi=ERC20_ABI,
            )
        return self._contract

    async def get_usdt_balance(self, address: str) -> float:
        """Get USDT balance for a BSC address."""
        try:
            checksum_addr = self.web3.to_checksum_address(address)
            balance_wei = self.usdt_contract.functions.balanceOf(checksum_addr).call()
            decimals = self.usdt_contract.functions.decimals().call()
            balance = balance_wei / (10 ** decimals)
            return float(balance)
        except Exception as e:
            logger.error(f"BSC balance check failed: {e}")
            return 0.0

    async def check_incoming_transfers(self, address: str, from_block: int = None) -> float:
        """Check for incoming USDT transfers to address."""
        try:
            checksum_addr = self.web3.to_checksum_address(address)
            if from_block is None:
                from_block = self.web3.eth.block_number - 100

            # Get Transfer events to our address
            transfer_filter = self.usdt_contract.events.Transfer.create_filter(
                fromBlock=from_block,
                argument_filters={"to": checksum_addr},
            )
            events = transfer_filter.get_all_entries()

            total_received = 0.0
            decimals = self.usdt_contract.functions.decimals().call()
            for event in events:
                amount = event["args"]["value"] / (10 ** decimals)
                total_received += amount

            return total_received
        except Exception as e:
            logger.error(f"BSC transfer check failed: {e}")
            return 0.0



class TRONChecker:
    """TRON/TRC20 payment verification using tronpy."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from tronpy import Tron
            from tronpy.providers import HTTPProvider
            if TRON_API_KEY:
                provider = HTTPProvider(TRON_RPC_URL, api_key=TRON_API_KEY)
            else:
                provider = HTTPProvider(TRON_RPC_URL)
            self._client = Tron(provider=provider)
        return self._client

    async def get_usdt_balance(self, address: str) -> float:
        """Get USDT (TRC20) balance for a TRON address."""
        try:
            contract = self.client.get_contract(TRON_USDT_CONTRACT)
            balance = contract.functions.balanceOf(address)
            # USDT on TRON has 6 decimals
            return float(balance) / 1_000_000
        except Exception as e:
            logger.error(f"TRON balance check failed: {e}")
            return 0.0

    async def check_incoming_transfers(self, address: str) -> float:
        """Check recent TRC20 transfers to address."""
        try:
            import httpx
            url = f"{TRON_RPC_URL}/v1/accounts/{address}/transactions/trc20"
            params = {
                "contract_address": TRON_USDT_CONTRACT,
                "only_to": "true",
                "limit": 20,
            }
            headers = {}
            if TRON_API_KEY:
                headers["TRON-PRO-API-KEY"] = TRON_API_KEY

            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, headers=headers)
                data = resp.json()

            total = 0.0
            for tx in data.get("data", []):
                value = int(tx.get("value", "0"))
                total += value / 1_000_000

            return total
        except Exception as e:
            logger.error(f"TRON transfer check failed: {e}")
            return 0.0


class PaymentVerifier:
    """Unified payment verification service."""

    def __init__(self):
        self.bsc = BSCChecker()
        self.tron = TRONChecker()

    async def check_payment(self, network: str, address: str) -> float:
        """Check payment received on the given network/address."""
        if network == "BSC":
            return await self.bsc.get_usdt_balance(address)
        elif network == "TRON":
            return await self.tron.get_usdt_balance(address)
        else:
            logger.warning(f"Unsupported network: {network}")
            return 0.0

    async def verify_deposit(self, network: str, address: str, expected_amount: float) -> bool:
        """Verify if expected deposit has been received."""
        received = await self.check_payment(network, address)
        return received >= expected_amount


# Global instance
payment_verifier = PaymentVerifier()
