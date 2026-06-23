"""Deposit-address generation for each supported network.

Every trade gets a freshly generated address so incoming payments can be
unambiguously matched to a single deal. The generated private keys are returned
so an operator can later sweep / forward funds, but **storing private keys in a
database is sensitive** - encrypt them at rest in production.

Networks
--------
- BEP20 (BSC)  -> Ethereum-style keypair (eth-account)
- TRC20 (TRON) -> Tron keypair (tronpy.keys)
- BITCOIN      -> P2PKH legacy address (pure-Python: ecdsa + base58)
- LITECOIN     -> P2PKH legacy address (pure-Python: ecdsa + base58)

All dependencies are pure-Python wheels, so no C/Rust toolchain is needed at
build/deploy time.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

from ..models import Network
from ._ripemd160 import ripemd160


@dataclass
class GeneratedAddress:
    address: str
    private_key: str
    network: Network


# --------------------------------------------------------------------- helpers
def _hash160(data: bytes) -> bytes:
    return ripemd160(hashlib.sha256(data).digest())


def _b58check(version: int, payload: bytes) -> str:
    import base58

    body = bytes([version]) + payload
    checksum = hashlib.sha256(hashlib.sha256(body).digest()).digest()[:4]
    return base58.b58encode(body + checksum).decode("ascii")


def _compressed_pubkey(private_key: bytes) -> bytes:
    """Derive the compressed secp256k1 public key for a 32-byte private key."""
    from ecdsa import SECP256k1, SigningKey

    sk = SigningKey.from_string(private_key, curve=SECP256k1)
    point = sk.verifying_key.pubkey.point
    x = point.x().to_bytes(32, "big")
    prefix = b"\x03" if (point.y() & 1) else b"\x02"
    return prefix + x


# --------------------------------------------------------------------- chains
def _generate_evm() -> GeneratedAddress:
    from eth_account import Account

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


def _generate_btc_like(
    addr_version: int, wif_version: int, model_network: Network
) -> GeneratedAddress:
    private_key = os.urandom(32)
    pubkey = _compressed_pubkey(private_key)
    address = _b58check(addr_version, _hash160(pubkey))
    # Compressed WIF: version + 32-byte key + 0x01 compression flag
    wif = _b58check(wif_version, private_key + b"\x01")
    return GeneratedAddress(address=address, private_key=wif, network=model_network)


def generate_address(network: Network) -> GeneratedAddress:
    """Generate a brand-new deposit address for ``network``."""
    if network == Network.BEP20:
        return _generate_evm()
    if network == Network.TRC20:
        return _generate_tron()
    if network == Network.BITCOIN:
        # Bitcoin mainnet: P2PKH version 0x00, WIF 0x80
        return _generate_btc_like(0x00, 0x80, Network.BITCOIN)
    if network == Network.LITECOIN:
        # Litecoin mainnet: P2PKH version 0x30 ('L'), WIF 0xB0
        return _generate_btc_like(0x30, 0xB0, Network.LITECOIN)
    raise ValueError(f"Unsupported network: {network}")
