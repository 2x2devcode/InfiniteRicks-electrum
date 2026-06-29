# InfiniteRicks Electrum Wallet

Carteira leve (SPV) profissional para a criptomoeda **InfiniteRicks** (RICK).

> **Não é um fork da Electrum.** Arquitetura própria em Python, utilizando apenas os conceitos técnicos SPV: sincronização de block headers, Merkle proofs e comunicação com servidor ElectrumX.

## Características

- Carteira leve SPV — nunca baixa a blockchain inteira
- Sincronização via ElectrumX (`144.91.107.244:50002` TLS)
- BIP39 (12 palavras) + BIP32 derivação determinística
- Criptografia AES-256-GCM + Argon2id
- Assinatura local secp256k1 — chaves nunca saem do dispositivo
- Interface PySide6 (desktop) + APK Android 15+

## Instalação rápida

```bash
git clone https://github.com/2x2devcode/infinitericks-electrum.git
cd infinitericks-electrum
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Estrutura do projeto

```
infinitericks_wallet/
├── config/       # Parâmetros da rede InfiniteRicks
├── crypto/       # Scrypt, endereços, transações
├── wallet/       # BIP39/32, UTXO, assinatura
├── network/      # Cliente ElectrumX
├── spv/          # Sincronização SPV
├── gui/          # Interface PySide6
├── storage/      # Carteira criptografada
└── android/      # Build APK
docs/             # Documentação completa
tests/            # Testes automatizados
```

## Parâmetros da rede

Extraídos do repositório oficial [2x2devcode/InfiniteRicks](https://github.com/2x2devcode/InfiniteRicks):

| Parâmetro | Valor |
|-----------|-------|
| P2P | 31647 |
| RPC | 31648 |
| P2PKH prefix | 0x00 (endereços `1...`) |
| Block hash | Scrypt N=1024, r=1, p=1 |
| Block time | 120s |
| COIN | 1e8 |

Ver `docs/CHAIN_ANALYSIS.md` para análise completa.

## Parâmetro ausente no repositório oficial

- **BIP44 coin type**: não definido — configurável em `config/chainparams.py`

## Testes

```bash
pytest tests/ -v
```

## Build Android

```bash
bash android/build_apk.sh
```

Ver `docs/INSTALL.md` e `docs/DEVELOPER.md`.

## Servidor ElectrumX (SPV)

Se a carteira mostra **No Connection**, o servidor SPV pode estar offline. Para instalar o seu:

```bash
# Guia completo
cat docs/ELECTRUMX_SETUP.md
```

Teste de conectividade: `python scripts/check_spv_server.py`

## Links

- Site: https://infinitericks.com
- Explorer: https://explorer.infinitericks.com
- Servidor SPV: `144.91.107.244:50002`

## Licença

MIT — ver LICENSE
