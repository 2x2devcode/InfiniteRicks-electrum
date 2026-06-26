"""Block header parsing and validation."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Optional

from infinitericks_wallet.config.chainparams import ACTIVE_NETWORK, NetworkParams
from infinitericks_wallet.crypto.scrypt_hash import scrypt_blockhash_hex


def uint256_from_hex(hex_str: str) -> bytes:
    """Convert display-order hex hash to internal serialization bytes."""
    return bytes.fromhex(hex_str)[::-1]


def uint256_to_hex(data: bytes) -> str:
    """Convert internal bytes to display-order hex."""
    return data[::-1].hex()


@dataclass
class BlockHeader:
    version: int
    prev_block: bytes
    merkle_root: bytes
    timestamp: int
    bits: int
    nonce: int
    height: int = 0

    HEADER_SIZE = 80

    def serialize(self) -> bytes:
        return (
            struct.pack("<i", self.version)
            + self.prev_block
            + self.merkle_root
            + struct.pack("<III", self.timestamp, self.bits, self.nonce)
        )

    @classmethod
    def deserialize(cls, data: bytes, height: int = 0) -> "BlockHeader":
        if len(data) < 80:
            raise ValueError("Header must be 80 bytes")
        version = struct.unpack_from("<i", data, 0)[0]
        prev_block = data[4:36]
        merkle_root = data[36:68]
        timestamp, bits, nonce = struct.unpack_from("<III", data, 68)
        return cls(version, prev_block, merkle_root, timestamp, bits, nonce, height)

    def hash_hex(self) -> str:
        return scrypt_blockhash_hex(self.serialize())

    def verify_pow(self) -> bool:
        from infinitericks_wallet.crypto.scrypt_hash import compact_to_target, scrypt_blockhash

        target = compact_to_target(self.bits)
        hash_int = int.from_bytes(scrypt_blockhash(self.serialize()), "little")
        return hash_int <= target

    def verify_checkpoint(self, network: NetworkParams = ACTIVE_NETWORK) -> bool:
        if self.height in network.checkpoints:
            return self.hash_hex() == network.checkpoints[self.height]
        return True


def parse_electrum_header(hex_header: str, height: int) -> BlockHeader:
    """Parse header from ElectrumX hex string (80 bytes)."""
    return BlockHeader.deserialize(bytes.fromhex(hex_header), height)
