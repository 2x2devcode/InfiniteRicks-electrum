"""Tests for scrypt block hash and SPV headers."""

import struct

from infinitericks_wallet.crypto.block import BlockHeader, uint256_from_hex
from infinitericks_wallet.crypto.scrypt_hash import scrypt_blockhash_hex, pow_limit_compact
from infinitericks_wallet.config.chainparams import MAINNET


def test_genesis_block_hash():
    merkle = uint256_from_hex(MAINNET.genesis_merkle_root)
    n_bits = pow_limit_compact()
    header = struct.pack("<I", 1) + bytes(32) + merkle + struct.pack(
        "<III", MAINNET.genesis_time, n_bits, MAINNET.genesis_nonce
    )
    assert scrypt_blockhash_hex(header) == MAINNET.genesis_hash


def test_header_serialization_size():
    h = BlockHeader(1, bytes(32), bytes(32), 1585247880, 0x1e0fffff, 1125206)
    assert len(h.serialize()) == 80
