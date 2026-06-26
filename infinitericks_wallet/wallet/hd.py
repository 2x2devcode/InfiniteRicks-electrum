"""BIP32 hierarchical deterministic key derivation."""

from __future__ import annotations

import hashlib
import hmac
import struct
from dataclasses import dataclass
from typing import List, Tuple

from infinitericks_wallet.config.chainparams import (
    BIP44_ACCOUNT,
    BIP44_CHANGE_EXTERNAL,
    BIP44_COIN_TYPE,
    BIP44_PURPOSE,
    get_derivation_path,
)
from infinitericks_wallet.crypto.hash import hash160
from infinitericks_wallet.crypto.keys import KeyPair

CURVE_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


@dataclass
class HDKey:
    private_key: bytes
    chain_code: bytes
    depth: int = 0
    index: int = 0
    parent_fingerprint: bytes = b"\x00\x00\x00\x00"

    def fingerprint(self) -> bytes:
        pubkey = KeyPair.from_private_bytes(self.private_key).public_key
        return hash160(pubkey)[:4]

    def derive_child(self, index: int) -> "HDKey":
        if index >= 0x80000000:
            data = b"\x00" + self.private_key + struct.pack(">I", index)
        else:
            pubkey = KeyPair.from_private_bytes(self.private_key).public_key
            data = pubkey + struct.pack(">I", index)
        h = hmac.new(self.chain_code, data, hashlib.sha512).digest()
        child_key_int = (int.from_bytes(self.private_key, "big") + int.from_bytes(h[:32], "big")) % CURVE_ORDER
        return HDKey(
            child_key_int.to_bytes(32, "big"),
            h[32:],
            self.depth + 1,
            index,
            self.fingerprint(),
        )

    def derive_path(self, path: str) -> "HDKey":
        key = self
        parts = path.lstrip("m/").split("/")
        for part in parts:
            hardened = part.endswith("'")
            index = int(part.rstrip("'"))
            if hardened:
                index += 0x80000000
            key = key.derive_child(index)
        return key

    def keypair(self) -> KeyPair:
        return KeyPair.from_private_bytes(self.private_key)


def master_key_from_seed(seed: bytes) -> HDKey:
    h = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
    return HDKey(h[:32], h[32:])


def derive_address_key(master: HDKey, change: int = BIP44_CHANGE_EXTERNAL, index: int = 0) -> Tuple[HDKey, str]:
    path = get_derivation_path(change, index)
    child = master.derive_path(path)
    return child, path
