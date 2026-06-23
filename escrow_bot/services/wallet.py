"""Deposit-address generation for each supported network.

Every trade gets a freshly generated address so incoming payments can be
unambiguously matched to a single deal. The generated private keys are returned
so an operator can later sweep / forward funds, but **storing private keys in a
database is sensitive** - encrypt them at rest in production.

Networks
--------
- BEP20 (BSC)  -> Ethereum-style keypair (eth-account)
- TRC20 (TRON) -> Tron keypair (tronpy.keys)
- BITCOIN      -> P2WPKH/P2PKH key (bitcoinlib)
- LITECOIN     -> Litecoin key (bitcoinlib)
"""

from __future__ import annotations

from dataclasses import dataclass

from ..models import Network


@dataclass
class GeneratedAddress:
    address: str
    private_key: str
    network: Network


def _generate_evm() -> GeneratedAddress:
    from eth_account import Account

    Account.enable_unaudited_hdwallet_features()
    acct = Account.create()
    return GeneratedAddress(
        address=acct.address,
        private_key=acct.key.hex(),
        network=Network.BEP20,
    )


def _generate_tron() -> GeneratedAddress:
    from tronpy.keys import PrivateKey

    pk = PrivateKey.random()
    return GeneratedAddress(
        address=pk.public_key.to_base58check_address(),
        private_key=pk.hex(),
        network=Network.TRC20,
    )


def _generate_bitcoinlib(network_name: str, model_network: Network) -> GeneratedAddress:
    # bitcoinlib supports both bitcoin and litecoin networks
    from bitcoinlib.keys import Key

    key = Key(network=network_name)
    return GeneratedAddress(
        address=key.address(),
        private_key=key.wif(),
        network=model_network,
    )


def generate_address(network: Network) -> GeneratedAddress:
    """Generate a brand-new deposit address for ``network``."""
    if network == Network.BEP20:
        return _generate_evm()
    if network == Network.TRC20:
        return _generate_tron()
    if network == Network.BITCOIN:
        return _generate_bitcoinlib("bitcoin", Network.BITCOIN)
    if network == Network.LITECOIN:
        return _generate_bitcoinlib("litecoin", Network.LITECOIN)
    raise ValueError(f"Unsupported network: {network}")
