"""Chain parameters extracted from official InfiniteRicks repository.

Source: https://github.com/2x2devcode/InfiniteRicks
All values verified against source files — see docs/CHAIN_ANALYSIS.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class NetworkParams:
    name: str
    magic_bytes: bytes
    p2p_port: int
    rpc_port: int
    pubkey_address_prefix: int
    script_address_prefix: int
    wif_prefix: int
    genesis_hash: str
    genesis_merkle_root: str
    genesis_time: int
    genesis_nonce: int
    checkpoints: Dict[int, str] = field(default_factory=dict)
    dns_seeds: List[str] = field(default_factory=list)


MAINNET = NetworkParams(
    name="mainnet",
    magic_bytes=bytes([0xC9, 0x09, 0x6E, 0x5A]),
    p2p_port=31647,
    rpc_port=31648,
    pubkey_address_prefix=0x00,
    script_address_prefix=0x55,
    wif_prefix=0x80,
    genesis_hash="0000040917e53132256572dbcd3f780e94d40b4a1895672bfd64e0c5c0741dc8",
    genesis_merkle_root="63f41eb2a1ad819aace407b1694e05e09cc6503fea38dc7a9302ce07bbba4c07",
    genesis_time=1585247880,
    genesis_nonce=1125206,
    checkpoints={
        0: "0000040917e53132256572dbcd3f780e94d40b4a1895672bfd64e0c5c0741dc8",
    },
    dns_seeds=[
        "104.28.196.77", "104.28.196.78", "104.28.228.77", "104.28.228.78",
        "109.163.219.243", "167.86.78.55", "180.75.245.223", "181.45.56.131",
    ],
)

TESTNET = NetworkParams(
    name="testnet",
    magic_bytes=bytes([0x70, 0x6E, 0x7D, 0x0A]),
    p2p_port=41647,
    rpc_port=41648,
    pubkey_address_prefix=0x6F,
    script_address_prefix=0xC4,
    wif_prefix=0xEF,
    genesis_hash="0000092a064f16a4a86c69c49084ee58c25858d6b05aea56c2ce8318d3174738",
    genesis_merkle_root="63f41eb2a1ad819aace407b1694e05e09cc6503fea38dc7a9302ce07bbba4c07",
    genesis_time=1585247880,
    genesis_nonce=125242,
    checkpoints={
        0: "0000092a064f16a4a86c69c49084ee58c25858d6b05aea56c2ce8318d3174738",
        5720: "41bed32902d5f95e1cb9d550008251f86744bb27dd0eb7d6ba377d43198ec228",
        115000: "2c223d88154c9d8cc062ace3d6002288d458e6ff034a2397939540fce7542bad",
        251106: "2410cff3bf2fe8ef1589ecb8965ed1e45c4bfff744912e51a20e5caf288ffdb7",
        406666: "e0ea780adb7dc615b9b7cd4880cb269ea84f8c8e7271d23cbe6f4cfc8fefbeff",
        690100: "2b8edeb5bf938854243a3f49571023708433ca231480cc9e840b690448568a12",
        851250: "b46015acbc8108a3875356b94ca1a62d809cd60ad4da7fb6d808897eb6d29557",
        1000250: "138290a9a09b82ec500116beb5f919a24ff4024e78d77147017f9010dbf88bdd",
        1330250: "9fd3b78d8ee0852ba523d89d39c9edd95357b28b5d49582941e874c4f24e2d67",
    },
)

# Consensus constants — src/main.h, src/main.cpp
COIN = 100_000_000
CENT = 1_000_000
MIN_TX_FEE = 10_000
MIN_RELAY_TX_FEE = 10_000
LOCKTIME_THRESHOLD = 500_000_000
LAST_POW_BLOCK = 3000
BLOCK_TARGET_SPACING = 120
COINBASE_MATURITY = 24
STAKE_MIN_AGE = 12 * 60 * 60
COIN_YEAR_REWARD = 307 * CENT
POW_SUBSIDY = 1000 * COIN
TX_VERSION = 1
BLOCK_VERSION = 6
PROTOCOL_VERSION = 60015

# Message signing — src/main.cpp
MESSAGE_MAGIC = "InfiniteRicks Signed Message:\n"

# BIP44 coin type — NOT defined in official InfiniteRicks repository.
# Configurable for future SLIP-0044 registration.
BIP44_COIN_TYPE = 0
BIP44_PURPOSE = 44
BIP44_ACCOUNT = 0
BIP44_CHANGE_EXTERNAL = 0
BIP44_CHANGE_INTERNAL = 1

# ElectrumX servers
ELECTRUM_SERVERS: List[Tuple[str, int, bool]] = [
    ("144.91.107.244", 50002, True),
]

ELECTRUM_PROTOCOL_VERSION = ("1.4", "1.4.2")

# Application URLs
WEBSITE_URL = "https://infinitericks.com"
EXPLORER_URL = "https://explorer.infinitericks.com"

# Fee tiers (satoshis per byte)
FEE_RATE_NORMAL = 10
FEE_RATE_FAST = 25

# Wallet encryption
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65536  # 64 MiB
ARGON2_PARALLELISM = 4
ARGON2_HASH_LEN = 32
ARGON2_SALT_LEN = 16

# Network client
CONNECT_TIMEOUT = 30
REQUEST_TIMEOUT = 60
MAX_RECONNECT_ATTEMPTS = 10
RECONNECT_DELAY_BASE = 2.0

# Active network (switchable)
ACTIVE_NETWORK: NetworkParams = MAINNET


def get_derivation_path(change: int = 0, index: int = 0) -> str:
    """BIP44 derivation path. Coin type is configurable — not in official repo."""
    return f"m/{BIP44_PURPOSE}'/{BIP44_COIN_TYPE}'/{BIP44_ACCOUNT}'/{change}/{index}"
