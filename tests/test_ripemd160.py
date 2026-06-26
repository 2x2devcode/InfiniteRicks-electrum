"""RIPEMD-160 fallback tests."""

from infinitericks_wallet.crypto.hash import hash160
from infinitericks_wallet.crypto.ripemd160 import ripemd160_digest


def test_ripemd160_vectors():
    assert ripemd160_digest(b"").hex() == "9c1185a5c5e9fc54612808977ee8f548b2258d31"
    assert ripemd160_digest(b"abc").hex() == "8eb208f7e05d987a9b044a8e98c6b087f15a0bfc"


def test_hash160():
    h = hash160(b"test")
    assert len(h) == 20
