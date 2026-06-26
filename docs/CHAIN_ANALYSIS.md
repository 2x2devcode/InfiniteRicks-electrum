# InfiniteRicks Chain Analysis

Source repository: https://github.com/2x2devcode/InfiniteRicks  
Analysis date: 2026-06-26

## Network (Mainnet)

| Parameter | Value | Source |
|-----------|-------|--------|
| Magic bytes | `c9 09 6e 5a` | `src/main.cpp:2849` |
| P2P port | 31647 | `src/protocol.h` |
| RPC port | 31648 | `src/bitcoinrpc.cpp` |
| Protocol version | 60015 | `src/version.h` |
| Ticker | RICK | `README.md` |
| COIN | 100000000 (1e8) | `src/util.h` |

## Network (Testnet)

| Parameter | Value |
|-----------|-------|
| Magic | `70 6e 7d 0a` |
| P2P port | 41647 |
| RPC port | 41648 |

## Genesis Block (Mainnet)

| Field | Value |
|-------|-------|
| Hash | `0000040917e53132256572dbcd3f780e94d40b4a1895672bfd64e0c5c0741dc8` |
| Merkle root | `63f41eb2a1ad819aace407b1694e05e09cc6503fea38dc7a9302ce07bbba4c07` |
| nTime | 1585247880 |
| nNonce | 1125206 |
| Coinbase | "Nobody exists on purpose Moooorty" |

## Address Format

| Type | Mainnet prefix | Testnet prefix |
|------|----------------|----------------|
| P2PKH | 0x00 (starts with `1`) | 0x6F |
| P2SH | 0x55 | 0xC4 |
| WIF | 0x80 | 0xEF |

No Bech32/SegWit support in official codebase.

## Hash Algorithms

| Purpose | Algorithm |
|---------|-----------|
| Block hash | Scrypt (N=1024, r=1, p=1) on 80-byte header |
| Transaction ID | Double SHA-256 |
| Merkle tree | Double SHA-256 pairwise |
| Message signing | SHA256d of `"InfiniteRicks Signed Message:\n" + message` |

## Consensus

- Peercoin-style PoW + PoS hybrid
- PoW ends at block 3000 (`LAST_POW_BLOCK`)
- Block time target: 120 seconds
- Min stake age: 12 hours (mainnet)
- PoS reward: `nCoinAge * COIN_YEAR_REWARD * 33 / (365 * 33 + 8)`
- `COIN_YEAR_REWARD = 307 * CENT` (307% APR basis)

## Transaction Format

Serialization order (Peercoin extension):

```
nVersion → nTime → vin[] → vout[] → nLockTime
```

`CURRENT_VERSION = 1`, includes `nTime` field (not in Bitcoin).

## Checkpoints (Mainnet)

- Height 0: genesis hash only

## Checkpoints (Testnet)

Heights: 0, 5720, 115000, 251106, 406666, 690100, 851250, 1000250, 1330250

## SPV Considerations

1. Block headers use Scrypt PoW hash (80 bytes), not double-SHA256
2. After height 3000 all blocks are PoS — header-only validation is limited
3. Chain selection uses `nChainTrust`, not cumulative work
4. No BIP37/filtered blocks in official P2P — ElectrumX custom server required
5. Synchronized checkpoints enforced on mainnet

## Missing from Official Repository

| Parameter | Status |
|-----------|--------|
| BIP44 coin type | **NOT DEFINED** — must be configured in wallet |
| ElectrumX protocol spec | **NOT IN REPO** — uses standard Electrum protocol |
| SLIP-0044 registration | **NOT FOUND** |
