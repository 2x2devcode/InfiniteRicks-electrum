"""Encrypted wallet storage with AES-256-GCM and Argon2id."""

from __future__ import annotations

import json
import os
import secrets
from pathlib import Path
from typing import Optional

from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from infinitericks_wallet.config.chainparams import (
    ARGON2_HASH_LEN,
    ARGON2_MEMORY_COST,
    ARGON2_PARALLELISM,
    ARGON2_SALT_LEN,
    ARGON2_TIME_COST,
)
from infinitericks_wallet.wallet.wallet import Wallet

WALLET_VERSION = 1


class EncryptedStore:
    def __init__(self, path: Optional[Path] = None) -> None:
        self._path = path or Path.home() / ".infinitericks_wallet" / "wallet.enc"
        self._path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def exists(self) -> bool:
        return self._path.exists()

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        return hash_secret_raw(
            secret=password.encode("utf-8"),
            salt=salt,
            time_cost=ARGON2_TIME_COST,
            memory_cost=ARGON2_MEMORY_COST,
            parallelism=ARGON2_PARALLELISM,
            hash_len=ARGON2_HASH_LEN,
            type=Type.ID,
        )

    def save(self, wallet: Wallet, password: str) -> None:
        salt = secrets.token_bytes(ARGON2_SALT_LEN)
        key = self._derive_key(password, salt)
        nonce = secrets.token_bytes(12)
        plaintext = json.dumps({"version": WALLET_VERSION, "wallet": wallet.to_dict()}).encode("utf-8")
        ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
        payload = {
            "version": WALLET_VERSION,
            "salt": salt.hex(),
            "nonce": nonce.hex(),
            "ciphertext": ciphertext.hex(),
        }
        self._path.write_text(json.dumps(payload))

    def load(self, password: str) -> Wallet:
        if not self.exists:
            raise FileNotFoundError("Wallet file not found")
        payload = json.loads(self._path.read_text())
        salt = bytes.fromhex(payload["salt"])
        nonce = bytes.fromhex(payload["nonce"])
        ciphertext = bytes.fromhex(payload["ciphertext"])
        key = self._derive_key(password, salt)
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
        data = json.loads(plaintext.decode("utf-8"))
        wallet = Wallet()
        wallet.load_dict(data["wallet"])
        return wallet

    def change_password(self, old_password: str, new_password: str) -> None:
        wallet = self.load(old_password)
        self.save(wallet, new_password)

    def delete(self) -> None:
        if self._path.exists():
            os.remove(self._path)
