"""BIP39 mnemonic generation and validation."""

from __future__ import annotations

import secrets
from typing import List, Tuple

from mnemonic import Mnemonic

_MNEMONIC = Mnemonic("english")


def generate_mnemonic(strength: int = 128) -> str:
    """Generate 12-word (128-bit) or 24-word (256-bit) mnemonic."""
    return _MNEMONIC.generate(strength=strength)


def validate_mnemonic(words: str) -> bool:
    return _MNEMONIC.check(words.strip())


def mnemonic_to_seed(mnemonic: str, passphrase: str = "") -> bytes:
    return _MNEMONIC.to_seed(mnemonic, passphrase)


def split_mnemonic(mnemonic: str) -> List[str]:
    return mnemonic.strip().split()
