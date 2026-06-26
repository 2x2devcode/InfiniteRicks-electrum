"""Scrypt block hash — ported from InfiniteRicks src/scrypt.cpp (N=1024, r=1, p=1)."""

from __future__ import annotations

import hashlib
import hmac
import struct
from typing import List


def _rotl32(x: int, n: int) -> int:
    x &= 0xFFFFFFFF
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF


def _xor_salsa8(b: List[int], b_off: int, bx_off: int) -> None:
    x = []
    for i in range(16):
        b[b_off + i] = (b[b_off + i] ^ b[bx_off + i]) & 0xFFFFFFFF
        x.append(b[b_off + i])
    for _ in range(4):
        x[4] = (x[4] ^ _rotl32(x[0] + x[12], 7)) & 0xFFFFFFFF
        x[9] = (x[9] ^ _rotl32(x[5] + x[1], 7)) & 0xFFFFFFFF
        x[14] = (x[14] ^ _rotl32(x[10] + x[6], 7)) & 0xFFFFFFFF
        x[3] = (x[3] ^ _rotl32(x[15] + x[11], 7)) & 0xFFFFFFFF

        x[8] = (x[8] ^ _rotl32(x[4] + x[0], 9)) & 0xFFFFFFFF
        x[13] = (x[13] ^ _rotl32(x[9] + x[5], 9)) & 0xFFFFFFFF
        x[2] = (x[2] ^ _rotl32(x[14] + x[10], 9)) & 0xFFFFFFFF
        x[7] = (x[7] ^ _rotl32(x[3] + x[15], 9)) & 0xFFFFFFFF

        x[12] = (x[12] ^ _rotl32(x[8] + x[4], 13)) & 0xFFFFFFFF
        x[1] = (x[1] ^ _rotl32(x[13] + x[9], 13)) & 0xFFFFFFFF
        x[6] = (x[6] ^ _rotl32(x[2] + x[14], 13)) & 0xFFFFFFFF
        x[11] = (x[11] ^ _rotl32(x[7] + x[3], 13)) & 0xFFFFFFFF

        x[0] = (x[0] ^ _rotl32(x[12] + x[8], 18)) & 0xFFFFFFFF
        x[5] = (x[5] ^ _rotl32(x[1] + x[13], 18)) & 0xFFFFFFFF
        x[10] = (x[10] ^ _rotl32(x[6] + x[2], 18)) & 0xFFFFFFFF
        x[15] = (x[15] ^ _rotl32(x[11] + x[7], 18)) & 0xFFFFFFFF

        x[1] = (x[1] ^ _rotl32(x[0] + x[3], 7)) & 0xFFFFFFFF
        x[6] = (x[6] ^ _rotl32(x[5] + x[4], 7)) & 0xFFFFFFFF
        x[11] = (x[11] ^ _rotl32(x[10] + x[9], 7)) & 0xFFFFFFFF
        x[12] = (x[12] ^ _rotl32(x[15] + x[14], 7)) & 0xFFFFFFFF

        x[2] = (x[2] ^ _rotl32(x[1] + x[0], 9)) & 0xFFFFFFFF
        x[7] = (x[7] ^ _rotl32(x[6] + x[5], 9)) & 0xFFFFFFFF
        x[8] = (x[8] ^ _rotl32(x[11] + x[10], 9)) & 0xFFFFFFFF
        x[13] = (x[13] ^ _rotl32(x[12] + x[15], 9)) & 0xFFFFFFFF

        x[3] = (x[3] ^ _rotl32(x[2] + x[1], 13)) & 0xFFFFFFFF
        x[4] = (x[4] ^ _rotl32(x[7] + x[6], 13)) & 0xFFFFFFFF
        x[9] = (x[9] ^ _rotl32(x[8] + x[11], 13)) & 0xFFFFFFFF
        x[14] = (x[14] ^ _rotl32(x[13] + x[12], 13)) & 0xFFFFFFFF

        x[0] = (x[0] ^ _rotl32(x[3] + x[2], 18)) & 0xFFFFFFFF
        x[5] = (x[5] ^ _rotl32(x[4] + x[7], 18)) & 0xFFFFFFFF
        x[10] = (x[10] ^ _rotl32(x[9] + x[8], 18)) & 0xFFFFFFFF
        x[15] = (x[15] ^ _rotl32(x[14] + x[13], 18)) & 0xFFFFFFFF

    for i in range(16):
        b[b_off + i] = (b[b_off + i] + x[i]) & 0xFFFFFFFF


def _scrypt_core(x_words: List[int], v: List[int]) -> None:
    x = list(x_words)
    for i in range(1024):
        v[i * 32:(i + 1) * 32] = x[:32]
        _xor_salsa8(x, 0, 16)
        _xor_salsa8(x, 16, 0)
    for _ in range(1024):
        j = 32 * (x[16] & 1023)
        for k in range(32):
            x[k] ^= v[j + k]
        _xor_salsa8(x, 0, 16)
        _xor_salsa8(x, 16, 0)
    x_words[:] = x


def _pbkdf2_sha256(password: bytes, salt: bytes, rounds: int, dk_len: int) -> bytes:
    def _hmac_sha256(key: bytes, msg: bytes) -> bytes:
        return hmac.new(key, msg, hashlib.sha256).digest()

    block_count = (dk_len + 31) // 32
    result = b""
    for block_num in range(1, block_count + 1):
        u = _hmac_sha256(password, salt + struct.pack(">I", block_num))
        t = u
        for _ in range(rounds - 1):
            u = _hmac_sha256(password, u)
            t = bytes(a ^ b for a, b in zip(t, u))
        result += t
    return result[:dk_len]


def scrypt_blockhash(header: bytes) -> bytes:
    """Compute block hash from 80-byte header using InfiniteRicks scrypt algorithm."""
    if len(header) != 80:
        raise ValueError("Block header must be exactly 80 bytes")
    x = _pbkdf2_sha256(header, header, 1, 128)
    x_words = list(struct.unpack("<32I", x))
    v = [0] * (1024 * 32)
    _scrypt_core(x_words, v)
    x_out = struct.pack("<32I", *x_words)
    return _pbkdf2_sha256(header, x_out, 1, 32)


def scrypt_blockhash_hex(header: bytes) -> str:
    return scrypt_blockhash(header)[::-1].hex()


def compact_to_target(n_bits: int) -> int:
    size = n_bits >> 24
    word = n_bits & 0x007FFFFF
    if size <= 3:
        return word >> (8 * (3 - size))
    return word << (8 * (size - 3))


def target_to_compact(target: int) -> int:
    if target <= 0:
        return 0
    size = (target.bit_length() + 7) // 8
    if size <= 3:
        compact = (target << (8 * (3 - size))) & 0x007FFFFF
    else:
        compact = (target >> (8 * (size - 3))) & 0x007FFFFF
    if compact & 0x00800000:
        compact >>= 8
        size += 1
    return compact | (size << 24)


def pow_limit_compact() -> int:
    """bnProofOfWorkLimit = ~uint256(0) >> 20 compact representation."""
    target = (1 << 256) - 1
    target >>= 20
    return target_to_compact(target)
