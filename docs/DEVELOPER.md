# Manual do Desenvolvedor

## Arquitetura

Ver `docs/ARCHITECTURE.md` para diagramas completos.

## Módulos principais

### `config/chainparams.py`
Todos os parâmetros da rede. **Nunca invente valores** — altere apenas com base no repositório oficial.

### `crypto/scrypt_hash.py`
Implementação do algoritmo Scrypt ArtForz (N=1024, r=1, p=1) usado no block hash.

### `network/electrum_client.py`
Cliente JSON-RPC ElectrumX sobre TLS com reconexão e failover.

### `spv/sync_manager.py`
Orquestra sincronização de headers, histórico e Merkle proofs.

### `storage/encrypted_store.py`
AES-256-GCM com chave derivada via Argon2id.

## Fluxo SPV

1. `blockchain.headers.subscribe` — recebe tip
2. `blockchain.block.headers` — baixa headers incrementais
3. Verifica cadeia scrypt + checkpoints
4. `blockchain.scripthash.subscribe` — monitora endereços
5. `blockchain.transaction.get` + `get_merkle` — verifica inclusão

## Executar testes

```bash
pytest tests/ -v --cov=infinitericks_wallet
```

## Adicionar servidor ElectrumX

```python
# config/chainparams.py
ELECTRUM_SERVERS = [
    ("144.91.107.244", 50002, True),
    ("backup.server.com", 50002, True),
]
```

## BIP44 coin type

Não definido no repositório oficial. Configure `BIP44_COIN_TYPE` quando registrado no SLIP-0044.

## Contribuindo

1. Fork o repositório
2. Crie branch `feature/sua-feature`
3. Execute testes
4. Abra Pull Request
