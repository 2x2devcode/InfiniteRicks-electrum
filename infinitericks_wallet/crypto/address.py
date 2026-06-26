"""InfiniteRicks address encoding and validation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from infinitericks_wallet.config.chainparams import ACTIVE_NETWORK, NetworkParams
from infinitericks_wallet.crypto.base58 import decode_check_full, encode_check
from infinitericks_wallet.crypto.hash import hash160
from infinitericks_wallet.crypto.script import p2pkh_script, script_to_scripthash


@dataclass
class Address:
    address: str
    script: bytes
    scripthash: str

    @classmethod
    def from_pubkey(cls, pubkey: bytes, network: NetworkParams = ACTIVE_NETWORK) -> "Address":
        script = p2pkh_script(hash160(pubkey))
        addr = pubkey_to_address(pubkey, network)
        return cls(addr, script, script_to_scripthash(script))

    @classmethod
    def from_string(cls, address: str, network: NetworkParams = ACTIVE_NETWORK) -> "Address":
        if not validate_address(address, network):
            raise ValueError(f"Invalid address: {address}")
        version, payload = decode_check_full(address)
        if version == network.pubkey_address_prefix:
            script = p2pkh_script(payload)
        elif version == network.script_address_prefix:
            script = bytes([0xA9, 0x14]) + payload + bytes([0x87])
        else:
            raise ValueError("Unsupported address type")
        return cls(address, script, script_to_scripthash(script))


def pubkey_to_address(pubkey: bytes, network: NetworkParams = ACTIVE_NETWORK) -> str:
    return encode_check(network.pubkey_address_prefix, hash160(pubkey))


def validate_address(address: str, network: NetworkParams = ACTIVE_NETWORK) -> bool:
    if not address or len(address) < 26 or len(address) > 35:
        return False
    try:
        version, payload = decode_check_full(address)
    except Exception:
        return False
    if version == network.pubkey_address_prefix and len(payload) == 20:
        return address[0] == "1" if network.name == "mainnet" else True
    if version == network.script_address_prefix and len(payload) == 20:
        return True
    return False


def address_to_scripthash(address: str, network: NetworkParams = ACTIVE_NETWORK) -> str:
    return Address.from_string(address, network).scripthash
