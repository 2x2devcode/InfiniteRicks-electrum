"""Merkle proof verification."""

from __future__ import annotations

from typing import List

from infinitericks_wallet.crypto.hash import compute_merkle_root, double_sha256


def verify_merkle_proof(
    tx_hash_hex: str,
    merkle_root_hex: str,
    block_height: int,
    merkle_branch: List[str],
    tx_pos: int,
) -> bool:
    """Verify transaction inclusion via Merkle branch from ElectrumX."""
    tx_hash = bytes.fromhex(tx_hash_hex)[::-1]
    current = tx_hash
    for sibling_hex in merkle_branch:
        sibling = bytes.fromhex(sibling_hex)[::-1]
        if tx_pos % 2 == 0:
            current = double_sha256(current + sibling)
        else:
            current = double_sha256(sibling + current)
        tx_pos //= 2
    computed_root = current[::-1].hex()
    return computed_root == merkle_root_hex
