"""secp256k1 key operations."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Optional, Tuple

from coincurve import PrivateKey, PublicKey

from infinitericks_wallet.crypto.hash import hash160


@dataclass
class KeyPair:
    private_key: bytes
    public_key: bytes

    @classmethod
    def generate(cls) -> "KeyPair":
        pk = PrivateKey()
        return cls(pk.secret, pk.public_key.format(compressed=True))

    @classmethod
    def from_private_bytes(cls, secret: bytes) -> "KeyPair":
        pk = PrivateKey(secret)
        return cls(pk.secret, pk.public_key.format(compressed=True))

    @classmethod
    def from_wif(cls, wif: str, wif_prefix: int = 0x80) -> "KeyPair":
        from infinitericks_wallet.crypto.base58 import decode

        raw = decode(wif)
        if raw[0] != wif_prefix:
            raise ValueError("Invalid WIF prefix")
        payload = raw[1:-4] if len(raw) > 34 else raw[1:]
        if len(payload) == 33 and payload[-1] == 0x01:
            payload = payload[:-1]
        return cls.from_private_bytes(payload)

    def pubkey_hash(self) -> bytes:
        return hash160(self.public_key)

    def sign(self, digest: bytes) -> bytes:
        if len(digest) != 32:
            digest = hashlib.sha256(digest).digest()
        pk = PrivateKey(self.private_key)
        return pk.sign(digest)

    def sign_der(self, digest: bytes, sighash_type: int = 1) -> bytes:
        sig = self.sign(digest)
        return sig + bytes([sighash_type])

    def to_wif(self, wif_prefix: int = 0x80, compressed: bool = True) -> str:
        from infinitericks_wallet.crypto.base58 import encode_check

        payload = self.private_key + (b"\x01" if compressed else b"")
        return encode_check(wif_prefix, payload)


def verify_signature(pubkey: bytes, digest: bytes, signature: bytes) -> bool:
    if len(digest) != 32:
        digest = hashlib.sha256(digest).digest()
    sig_bytes = signature[:-1] if len(signature) == 65 else signature
    try:
        return PublicKey(pubkey).verify(sig_bytes, digest)
    except Exception:
        return False
