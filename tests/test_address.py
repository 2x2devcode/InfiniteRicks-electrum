"""Tests for address encoding."""

from infinitericks_wallet.crypto.address import validate_address
from infinitericks_wallet.crypto.keys import KeyPair
from infinitericks_wallet.crypto.address import pubkey_to_address


def test_address_roundtrip():
    kp = KeyPair.generate()
    addr = pubkey_to_address(kp.public_key)
    assert addr.startswith("1")
    assert validate_address(addr)


def test_invalid_address():
    assert not validate_address("invalid")
    assert not validate_address("")
