"""Double SHA-256 and serialization helpers."""

from __future__ import annotations

import hashlib
import struct
from typing import Iterable, List, Union


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def double_sha256(data: bytes) -> bytes:
    return sha256(sha256(data))


def hash256_hex(data: bytes) -> str:
    return double_sha256(data)[::-1].hex()


def uint256_from_le(data: bytes) -> int:
    return int.from_bytes(data, "little")


def uint256_to_le(value: int) -> bytes:
    return value.to_bytes(32, "little")


def compact_size(n: int) -> bytes:
    if n < 0xFD:
        return struct.pack("<B", n)
    if n <= 0xFFFF:
        return struct.pack("<BH", 0xFD, n)
    if n <= 0xFFFFFFFF:
        return struct.pack("<BI", 0xFE, n)
    return struct.pack("<BQ", 0xFF, n)


def read_compact_size(data: bytes, offset: int = 0) -> tuple[int, int]:
    prefix = data[offset]
    if prefix < 0xFD:
        return prefix, offset + 1
    if prefix == 0xFD:
        return struct.unpack_from("<H", data, offset + 1)[0], offset + 3
    if prefix == 0xFE:
        return struct.unpack_from("<I", data, offset + 1)[0], offset + 5
    return struct.unpack_from("<Q", data, offset + 1)[0], offset + 9


def serialize_varint(n: int) -> bytes:
    return compact_size(n)


def serialize_bytes(data: bytes) -> bytes:
    return compact_size(len(data)) + data


def serialize_uint32(n: int) -> bytes:
    return struct.pack("<I", n)


def serialize_int32(n: int) -> bytes:
    return struct.pack("<i", n)


def serialize_int64(n: int) -> bytes:
    return struct.pack("<q", n)


def serialize_uint256(value: Union[int, bytes]) -> bytes:
    if isinstance(value, int):
        return uint256_to_le(value)
    if len(value) == 32:
        return value
    raise ValueError("uint256 must be 32 bytes or int")


def hash160(data: bytes) -> bytes:
    return hashlib.new("ripemd160", sha256(data)).digest()


def merkle_hash(left: bytes, right: bytes) -> bytes:
    return double_sha256(left + right)


def compute_merkle_root(hashes: List[bytes]) -> bytes:
    if not hashes:
        return bytes(32)
    layer = list(hashes)
    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer.append(layer[-1])
        layer = [merkle_hash(layer[i], layer[i + 1]) for i in range(0, len(layer), 2)]
    return layer[0]
