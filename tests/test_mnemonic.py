"""Tests for BIP39 mnemonic."""

from infinitericks_wallet.wallet.mnemonic import generate_mnemonic, mnemonic_to_seed, validate_mnemonic


def test_generate_mnemonic_12_words():
    words = generate_mnemonic(128)
    parts = words.split()
    assert len(parts) == 12
    assert validate_mnemonic(words)


def test_validate_invalid_mnemonic():
    assert not validate_mnemonic("abandon abandon abandon")


def test_mnemonic_to_seed_deterministic():
    m = "abandon " * 11 + "about"
    s1 = mnemonic_to_seed(m)
    s2 = mnemonic_to_seed(m)
    assert s1 == s2
    assert len(s1) == 64
