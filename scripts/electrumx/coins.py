# Copyright (c) 2016-2017, Neil Booth
# Copyright (c) 2017, the ElectrumX authors
#
# Minimal coins.py for InfiniteRicks ElectrumX — all other coins removed.
# Copy to: electrumx/src/electrumx/lib/coins.py

'''Module providing coin abstraction for InfiniteRicks only.'''

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Optional, Sequence, Type

import electrumx.lib.util as util
import electrumx.lib.tx as lib_tx
import electrumx.server.block_processor as block_proc
import electrumx.server.daemon as daemon
from electrumx.lib.hash import HASHX_LEN, Base58, double_sha256, hash_to_hex_str
from electrumx.lib.script import ScriptPubKey
from electrumx.lib.tx import Tx
from electrumx.server.session import ElectrumX


@dataclass(slots=True)
class Block:
    raw: bytes
    header: bytes
    transactions: Sequence[Tx]


class CoinError(Exception):
    '''Exception raised for coin-related errors.'''


class Coin:
    '''Base class of coin hierarchy.'''

    REORG_LIMIT = 200
    RPC_URL_REGEX = re.compile(r'.+@(\[[0-9a-fA-F:]+\]|[^:]+)(:[0-9]+)?')
    VALUE_PER_COIN = 100_000_000
    CHUNK_SIZE = 2016
    BASIC_HEADER_SIZE = 80
    STATIC_BLOCK_HEADERS = True
    SESSIONCLS = ElectrumX
    DESERIALIZER = lib_tx.Deserializer
    DAEMON = daemon.Daemon
    BLOCK_PROCESSOR = block_proc.BlockProcessor
    P2PKH_VERBYTE = bytes.fromhex("00")
    P2SH_VERBYTES = (bytes.fromhex("05"),)
    ENCODE_CHECK = Base58.encode_check
    DECODE_CHECK = Base58.decode_check
    GENESIS_HASH = (
        "0000040917e53132256572dbcd3f780e94d40b4a1895672bfd64e0c5c0741dc8"
    )
    GENESIS_ACTIVATION = 100_000_000
    DEFAULT_MAX_SEND = 8_100_000
    DEFAULT_MAX_RECV = 1_000_000
    PEER_DEFAULT_PORTS = {"t": "50001", "s": "50002"}
    PEERS = []
    CRASH_CLIENT_VER = None
    BLACKLIST_URL = None
    ESTIMATEFEE_MODES = (None, "CONSERVATIVE", "ECONOMICAL")
    MIN_REQUIRED_DAEMON_VERSION: Optional[str] = None
    REQUIRED_DAEMON_INDEXES: Sequence[str] = tuple()

    RPC_PORT: int
    NAME: str
    NET: str | None
    TX_COUNT_HEIGHT: int
    TX_COUNT: int
    TX_PER_BLOCK: int

    @classmethod
    def lookup_coin_class(cls, name: str, net: str) -> Type["Coin"]:
        req_attrs = ("TX_COUNT", "TX_COUNT_HEIGHT", "TX_PER_BLOCK")
        for coin in util.subclasses(Coin):
            if (
                coin.NAME.lower() == name.lower()
                and coin.NET is not None
                and coin.NET.lower() == net.lower()
            ):
                missing = [attr for attr in req_attrs if not hasattr(coin, attr)]
                if missing:
                    raise CoinError(f"coin {name} missing {missing} attributes")
                return coin
        raise CoinError(f"unknown coin {name} and network {net} combination")

    @classmethod
    def sanitize_url(cls, url: str) -> str:
        url = url.strip().rstrip("/")
        match = cls.RPC_URL_REGEX.match(url)
        if not match:
            raise CoinError(f'invalid daemon URL: "{url}"')
        if match.groups()[1] is None:
            url = f"{url}:{cls.RPC_PORT:d}"
        if not url.startswith(("http://", "https://")):
            url = f"http://{url}"
        return url + "/"

    @classmethod
    def max_fetch_blocks(cls, height: int) -> int:
        if height < 130_000:
            return 1000
        return 100

    @classmethod
    def genesis_block(cls, block: bytes) -> bytes:
        header = cls.block_header(block, 0)
        header_hex_hash = hash_to_hex_str(cls.header_hash_rev(header))
        if header_hex_hash != cls.GENESIS_HASH:
            raise CoinError(
                f"genesis block has hash {header_hex_hash} expected {cls.GENESIS_HASH}"
            )
        return header + b"\0"

    @classmethod
    def hashX_from_script(cls, script: bytes) -> bytes:
        return sha256(script).digest()[:HASHX_LEN]

    @classmethod
    def address_to_hashX(cls, address: str) -> bytes:
        return cls.hashX_from_script(cls.pay_to_address_script(address))

    @classmethod
    def hash160_to_P2PKH_script(cls, hash160: bytes) -> bytes:
        return ScriptPubKey.P2PKH_script(hash160)

    @classmethod
    def pay_to_address_script(cls, address: str) -> bytes:
        raw = cls.DECODE_CHECK(address)
        verbyte = -1
        verlen = len(raw) - 20
        if verlen > 0:
            verbyte, hash160 = raw[:verlen], raw[verlen:]
        if verbyte == cls.P2PKH_VERBYTE:
            return cls.hash160_to_P2PKH_script(hash160)
        if verbyte in cls.P2SH_VERBYTES:
            return ScriptPubKey.P2SH_script(hash160)
        raise CoinError(f"invalid address: {address}")

    @classmethod
    def header_hash_rev(cls, header: bytes) -> bytes:
        return double_sha256(header)

    @classmethod
    def header_prevhash_rev(cls, header: bytes) -> bytes:
        return header[4:36]

    @classmethod
    def static_header_offset(cls, height: int) -> int:
        assert cls.STATIC_BLOCK_HEADERS
        return height * cls.BASIC_HEADER_SIZE

    @classmethod
    def static_header_len(cls, height: int) -> int:
        return cls.static_header_offset(height + 1) - cls.static_header_offset(height)

    @classmethod
    def block_header(cls, block: bytes, height: int) -> bytes:
        return block[: cls.static_header_len(height)]

    @classmethod
    def block(cls, raw_block: bytes, height: int) -> Block:
        header = cls.block_header(raw_block, height)
        txs = cls.DESERIALIZER(raw_block, start=len(header)).read_tx_block()
        return Block(raw_block, header, txs)

    @classmethod
    def decimal_value(cls, value: int) -> Decimal:
        return Decimal(value) / cls.VALUE_PER_COIN

    @classmethod
    def warn_old_client_on_tx_broadcast(cls, _client_ver) -> bool:
        return False

    @classmethod
    def bucket_estimatefee_block_target(cls, n: int) -> int:
        return n


class ScryptMixin:
    """Scrypt block hash (N=1024, r=1, p=1) for version <= 6."""

    DESERIALIZER = lib_tx.DeserializerTxTime
    HEADER_HASH = None

    @classmethod
    def header_hash_rev(cls, header: bytes) -> bytes:
        if cls.HEADER_HASH is None:
            from hashlib import scrypt

            cls.HEADER_HASH = lambda x: scrypt(x, salt=x, n=1024, r=1, p=1, dklen=32)

        version, = util.unpack_le_uint32_from(header)
        if version > 6:
            return super().header_hash_rev(header)
        return cls.HEADER_HASH(header)


class InfiniteRicks(ScryptMixin, Coin):
    """InfiniteRicks mainnet — Peercoin-style nTime txs, Scrypt PoW headers."""

    NAME = "InfiniteRicks"
    SHORTNAME = "RICK"
    NET = "mainnet"
    P2PKH_VERBYTE = bytes.fromhex("00")
    P2SH_VERBYTES = (bytes.fromhex("55"),)
    WIF_BYTE = bytes.fromhex("80")
    GENESIS_HASH = (
        "0000040917e53132256572dbcd3f780e94d40b4a1895672bfd64e0c5c0741dc8"
    )
    DESERIALIZER = lib_tx.DeserializerTxTime
    TX_COUNT = 500_000
    TX_COUNT_HEIGHT = 200_000
    TX_PER_BLOCK = 2
    RPC_PORT = 31648
    REORG_LIMIT = 5000
    PEERS = []


class InfiniteRicksTestnet(ScryptMixin, Coin):
    """InfiniteRicks testnet."""

    NAME = "InfiniteRicks"
    SHORTNAME = "tRICK"
    NET = "testnet"
    P2PKH_VERBYTE = bytes.fromhex("6f")
    P2SH_VERBYTES = (bytes.fromhex("c4"),)
    WIF_BYTE = bytes.fromhex("ef")
    GENESIS_HASH = (
        "0000092a064f16a4a86c69c49084ee58c25858d6b05aea56c2ce8318d3174738"
    )
    DESERIALIZER = lib_tx.DeserializerTxTime
    TX_COUNT = 100_000
    TX_COUNT_HEIGHT = 50_000
    TX_PER_BLOCK = 2
    RPC_PORT = 41648
    REORG_LIMIT = 5000
    PEER_DEFAULT_PORTS = {"t": "51001", "s": "51002"}
    PEERS = []
