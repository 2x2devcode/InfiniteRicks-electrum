"""Base58Check encoding for InfiniteRicks addresses."""

from __future__ import annotations

import hashlib
from typing import Optional

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _checksum(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()[:4]


def encode(payload: bytes) -> str:
    num = int.from_bytes(payload, "big")
    encoded = ""
    while num > 0:
        num, rem = divmod(num, 58)
        encoded = ALPHABET[rem] + encoded
    for byte in payload:
        if byte == 0:
            encoded = "1" + encoded
        else:
            break
    return encoded


def decode(addr: str) -> bytes:
    num = 0
    for char in addr:
        num = num * 58 + ALPHABET.index(char)
    combined = num.to_bytes((num.bit_length() + 7) // 8 or 1, "big")
    pad = 0
    for char in addr:
        if char == "1":
            pad += 1
        else:
            break
    combined = b"\x00" * pad + combined
    if len(combined) < 5:
        raise ValueError("Invalid base58 address")
    payload, checksum = combined[:-4], combined[-4:]
    if _checksum(payload) != checksum:
        raise ValueError("Invalid base58 checksum")
    return payload


def encode_check(version: int, payload: bytes) -> str:
    data = bytes([version]) + payload
    return encode(data + _checksum(data))


def decode_check(addr: str) -> tuple[int, bytes]:
    payload = decode(addr)
    version, data = payload[0], payload[1:]
    if _checksum(bytes([version]) + data) != payload[-4:]:
        raise ValueError("Checksum mismatch")
    return version, data[:-4] if len(payload) > len(data) + 1 else data


def decode_check_full(addr: str) -> tuple[int, bytes]:
    raw = decode(addr)
    return raw[0], raw[1:]
