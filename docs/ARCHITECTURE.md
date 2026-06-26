# InfiniteRicks SPV Wallet — Architecture

## Overview

Lightweight Android/desktop wallet for InfiniteRicks (RICK). Uses SPV synchronization via ElectrumX-compatible servers. Private keys never leave the device.

**Not a fork of Electrum.** Original modular Python architecture reusing only SPV concepts.

## Module Diagram

```mermaid
graph TB
    subgraph GUI["gui/"]
        APP[app.py]
        WELCOME[welcome]
        HOME[home]
        DEPOSIT[deposit]
        SEND[send]
        TXS[transactions]
        SETTINGS[settings]
    end

    subgraph Core["wallet/ + crypto/"]
        WALLET[Wallet]
        HD[BIP32/BIP39]
        UTXO[UTXO Manager]
        SIGN[Transaction Signer]
        ADDR[Address]
        TX[Transaction]
    end

    subgraph SPV["spv/ + network/"]
        SYNC[SyncManager]
        HEADERS[HeaderStore]
        MERKLE[MerkleVerifier]
        REORG[ReorgHandler]
        CLIENT[ElectrumClient]
    end

    subgraph Storage["storage/"]
        ENC[EncryptedStore]
    end

    subgraph Config["config/"]
        PARAMS[chainparams]
    end

    APP --> WALLET
    APP --> SYNC
    WALLET --> HD
    WALLET --> UTXO
    WALLET --> SIGN
    SYNC --> CLIENT
    SYNC --> HEADERS
    SYNC --> MERKLE
    SYNC --> REORG
    WALLET --> ENC
    CLIENT --> PARAMS
    SIGN --> TX
    ADDR --> PARAMS
```

## SPV Sync Flow

```mermaid
sequenceDiagram
    participant W as Wallet
    participant S as SyncManager
    participant C as ElectrumClient
    participant H as HeaderStore

    W->>S: start_sync()
    S->>C: connect TLS
    C->>C: server.version
    S->>C: blockchain.headers.subscribe
    C-->>S: tip height + header
    S->>H: verify scrypt hash chain
    loop each address scripthash
        S->>C: blockchain.scripthash.subscribe
        C-->>S: status change
        S->>C: blockchain.scripthash.get_history
        C-->>S: tx hashes + heights
        S->>C: blockchain.transaction.get
        C-->>S: raw tx
        S->>C: blockchain.transaction.get_merkle
        C-->>S: merkle proof
        S->>S: verify merkle root vs header
    end
    S->>W: balance + history updated
```

## Wallet Creation Flow

```mermaid
flowchart TD
    A[Welcome Screen] -->|Create| B[Generate BIP39 12 words]
    B --> C[Show mnemonic + copy]
    C --> D[Verify 3 random positions]
    D -->|Wrong| B
    D -->|Correct| E[Set password]
    E --> F[Derive BIP32 master key]
    F --> G[Encrypt wallet AES-256-GCM + Argon2id]
    G --> H[Start SPV sync]
    A -->|Import| I[Enter 12 words]
    I --> J[Validate BIP39]
    J --> E
```

## Transaction Send Flow

```mermaid
flowchart TD
    A[Send Screen] --> B[Validate address]
    B --> C[Select UTXOs + fee tier]
    C --> D[Build unsigned tx]
    D --> E[Sign locally secp256k1]
    E --> F[User confirmation]
    F --> G[broadcast via ElectrumX]
    G -->|OK| H[Update history]
    G -->|Error| I[Show error]
```

## Folder Structure

```
infinitericks_wallet/
├── config/          # Chain parameters (from official repo)
├── crypto/          # Hash, scrypt, keys, addresses, transactions
├── wallet/          # BIP39/32, UTXO, signing, fees
├── network/         # ElectrumX JSON-RPC over TLS
├── spv/             # Header sync, merkle proofs, reorg
├── gui/             # PySide6 screens
├── storage/         # Encrypted wallet persistence
├── android/         # APK build (pyside6-android-deploy)
├── resources/       # Icons, QSS styles
├── tests/           # pytest suite
├── scripts/         # Build & utility scripts
└── docs/            # Documentation
```

## Security Model

| Layer | Technology |
|-------|------------|
| Wallet file encryption | AES-256-GCM |
| Key derivation | Argon2id (64 MiB, 3 iterations) |
| Seed | BIP39 12 words, never transmitted |
| Signing | secp256k1 ECDSA, local only |
| Network | TLS to ElectrumX server |

## Network Server

Primary: `144.91.107.244:50002` (SSL). Failover list extensible in `config/chainparams.py`.

## Parameters Source

All chain parameters extracted from [2x2devcode/InfiniteRicks](https://github.com/2x2devcode/InfiniteRicks). See `docs/CHAIN_ANALYSIS.md`.

## Missing Official Parameters

- **BIP44 coin type**: Not defined in official repository. Configurable via `BIP44_COIN_TYPE` in chainparams (default documented as user-configurable).
