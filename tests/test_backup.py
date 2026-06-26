"""Tests for wallet backup and restore."""

from infinitericks_wallet.wallet.wallet import Wallet


def test_create_and_restore_from_mnemonic():
    wallet1, mnemonic = Wallet.create_new()
    addr1 = wallet1.addresses[0].address

    wallet2 = Wallet()
    wallet2.load_from_mnemonic(mnemonic)
    addr2 = wallet2.addresses[0].address

    assert addr1 == addr2


def test_wallet_serialization_roundtrip():
    wallet, mnemonic = Wallet.create_new()
    wallet.generate_address("Second")
    data = wallet.to_dict()

    restored = Wallet()
    restored.load_dict(data)
    assert restored.mnemonic == mnemonic
    assert len(restored.addresses) == 2
