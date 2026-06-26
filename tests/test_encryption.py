"""Tests for encrypted wallet storage."""

import tempfile
from pathlib import Path

from infinitericks_wallet.storage.encrypted_store import EncryptedStore
from infinitericks_wallet.wallet.wallet import Wallet


def test_encrypt_decrypt_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "wallet.enc"
        store = EncryptedStore(path)
        wallet = Wallet()
        wallet.load_from_mnemonic("abandon " * 11 + "about")
        store.save(wallet, "testpassword123")
        loaded = store.load("testpassword123")
        assert loaded.mnemonic == wallet.mnemonic
        assert len(loaded.addresses) == len(wallet.addresses)


def test_wrong_password_fails():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "wallet.enc"
        store = EncryptedStore(path)
        wallet = Wallet()
        wallet.load_from_mnemonic("abandon " * 11 + "about")
        store.save(wallet, "correctpassword")
        try:
            store.load("wrongpassword")
            assert False, "Should have raised"
        except Exception:
            pass
