"""Bitcoin-style script helpers."""

from __future__ import annotations

import hashlib
from typing import List

from infinitericks_wallet.crypto.hash import hash256_hex, serialize_bytes, serialize_uint32


def p2pkh_script(pubkey_hash: bytes) -> bytes:
    return bytes([0x76, 0xA9, 0x14]) + pubkey_hash + bytes([0x88, 0xAC])


def script_to_scripthash(script: bytes) -> str:
    h = hashlib.sha256(script).digest()[::-1].hex()
    return h


def push_data(data: bytes) -> bytes:
    if len(data) < 0x4C:
        return bytes([len(data)]) + data
    if len(data) <= 0xFF:
        return bytes([0x4C, len(data)]) + data
    return bytes([0x4D]) + len(data).to_bytes(2, "little") + data


def make_p2pkh_scriptsig(signature: bytes, pubkey: bytes) -> bytes:
    return push_data(signature) + push_data(pubkey)
