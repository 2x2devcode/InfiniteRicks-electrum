"""Transaction serialization for InfiniteRicks (includes nTime field)."""

from __future__ import annotations

import struct
import time
from dataclasses import dataclass, field
from typing import List, Optional

from infinitericks_wallet.config.chainparams import TX_VERSION
from infinitericks_wallet.crypto.hash import double_sha256, hash256_hex, serialize_bytes, serialize_uint32, serialize_varint


@dataclass
class TxOut:
    value: int
    script_pubkey: bytes

    def serialize(self) -> bytes:
        return struct.pack("<q", self.value) + serialize_bytes(self.script_pubkey)

    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple["TxOut", int]:
        value = struct.unpack_from("<q", data, offset)[0]
        offset += 8
        script_len, offset = _read_varint(data, offset)
        script = data[offset:offset + script_len]
        return cls(value, script), offset + script_len


@dataclass
class TxIn:
    prev_hash: bytes
    prev_index: int
    script_sig: bytes
    sequence: int = 0xFFFFFFFF

    def serialize(self) -> bytes:
        return (
            self.prev_hash[::-1]
            + struct.pack("<I", self.prev_index)
            + serialize_bytes(self.script_sig)
            + struct.pack("<I", self.sequence)
        )

    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple["TxIn", int]:
        prev_hash = data[offset:offset + 32][::-1]
        offset += 32
        prev_index = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        script_len, offset = _read_varint(data, offset)
        script_sig = data[offset:offset + script_len]
        offset += script_len
        sequence = struct.unpack_from("<I", data, offset)[0]
        return cls(prev_hash, prev_index, script_sig, sequence), offset + 4


@dataclass
class Transaction:
    version: int = TX_VERSION
    n_time: int = 0
    inputs: List[TxIn] = field(default_factory=list)
    outputs: List[TxOut] = field(default_factory=list)
    locktime: int = 0

    def __post_init__(self) -> None:
        if self.n_time == 0:
            self.n_time = int(time.time())

    def serialize(self) -> bytes:
        parts = [
            struct.pack("<i", self.version),
            struct.pack("<I", self.n_time),
            serialize_varint(len(self.inputs)),
        ]
        parts.extend(inp.serialize() for inp in self.inputs)
        parts.append(serialize_varint(len(self.outputs)))
        parts.extend(out.serialize() for out in self.outputs)
        parts.append(struct.pack("<I", self.locktime))
        return b"".join(parts)

    def txid(self) -> str:
        return hash256_hex(self.serialize())

    @classmethod
    def deserialize(cls, data: bytes) -> "Transaction":
        offset = 0
        version = struct.unpack_from("<i", data, offset)[0]
        offset += 4
        n_time = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        in_count, offset = _read_varint(data, offset)
        inputs = []
        for _ in range(in_count):
            txin, offset = TxIn.deserialize(data, offset)
            inputs.append(txin)
        out_count, offset = _read_varint(data, offset)
        outputs = []
        for _ in range(out_count):
            txout, offset = TxOut.deserialize(data, offset)
            outputs.append(txout)
        locktime = struct.unpack_from("<I", data, offset)[0]
        return cls(version, n_time, inputs, outputs, locktime)

    def copy(self) -> "Transaction":
        return Transaction(
            self.version,
            self.n_time,
            [TxIn(i.prev_hash, i.prev_index, i.script_sig, i.sequence) for i in self.inputs],
            [TxOut(o.value, o.script_pubkey) for o in self.outputs],
            self.locktime,
        )


def _read_varint(data: bytes, offset: int) -> tuple[int, int]:
    prefix = data[offset]
    if prefix < 0xFD:
        return prefix, offset + 1
    if prefix == 0xFD:
        return struct.unpack_from("<H", data, offset + 1)[0], offset + 3
    if prefix == 0xFE:
        return struct.unpack_from("<I", data, offset + 1)[0], offset + 5
    return struct.unpack_from("<Q", data, offset + 1)[0], offset + 9


def signature_hash(tx: Transaction, input_index: int, script_code: bytes, sighash_type: int = 1) -> bytes:
    tx_copy = tx.copy()
    for i, inp in enumerate(tx_copy.inputs):
        tx_copy.inputs[i].script_sig = b"" if i != input_index else script_code

    if sighash_type & 0x1F == 2:  # SIGHASH_NONE
        tx_copy.outputs = []
        for i in range(len(tx_copy.inputs)):
            if i != input_index:
                tx_copy.inputs[i].sequence = 0
    elif sighash_type & 0x1F == 3:  # SIGHASH_SINGLE
        if input_index >= len(tx_copy.outputs):
            return b"\x00" * 32
        tx_copy.outputs = tx_copy.outputs[: input_index + 1]
        for i in range(input_index):
            tx_copy.outputs[i] = TxOut(0, b"")
        for i in range(len(tx_copy.inputs)):
            if i != input_index:
                tx_copy.inputs[i].sequence = 0

    if sighash_type & 0x80:  # ANYONECANPAY
        tx_copy.inputs = [tx_copy.inputs[input_index]]
        input_index = 0

    serialized = tx_copy.serialize() + struct.pack("<I", sighash_type)
    return double_sha256(serialized)
