# Guia: Instalar ElectrumX para InfiniteRicks

Este guia configura um servidor **SPV ElectrumX** para a carteira InfiniteRicks Electrum Wallet se conectar.

**Arquitetura:**

```
Carteira (desktop/APK)  ──TLS:50002──►  ElectrumX  ──RPC:31648──►  InfiniteRicksd (nó completo)
```

A carteira **não** fala com o daemon diretamente — só com ElectrumX.

---

## Requisitos

| Item | Mínimo recomendado |
|------|-------------------|
| SO | Ubuntu 22.04 LTS (VPS) |
| RAM | 4 GB (ElectrumX indexa a blockchain) |
| Disco | 20 GB+ livres |
| Rede | IP público (se carteiras externas vão conectar) |
| Portas | `31647` P2P, `31648` RPC (local), `50001`/`50002` ElectrumX |

---

## Parte 1 — Nó InfiniteRicks (`InfiniteRicksd`)

### 1.1 Dependências de compilação

```bash
sudo apt update
sudo apt install -y build-essential libssl-dev libboost-all-dev git
```

> **Nota:** O código oficial em [2x2devcode/InfiniteRicks](https://github.com/2x2devcode/InfiniteRicks) é antigo (fork Peercoin). Em Ubuntu 22.04 pode exigir patches de OpenSSL/Boost. Se já tiver o binário `InfiniteRicksd`, pule para 1.3.

### 1.2 Compilar (se necessário)

```bash
cd ~
git clone https://github.com/2x2devcode/InfiniteRicks.git
cd InfiniteRicks/src
make -f makefile.unix
sudo cp InfiniteRicksd /usr/local/bin/
```

### 1.3 Arquivo de configuração

```bash
mkdir -p ~/.InfiniteRicks
nano ~/.InfiniteRicks/InfiniteRicks.conf
```

Conteúdo mínimo:

```ini
daemon=1
server=1
txindex=1
rpcuser=rick_rpc_user
rpcpassword=TROQUE_POR_SENHA_FORTE_AQUI
rpcallowip=127.0.0.1
rpcport=31648
port=31647
```

`txindex=1` é **obrigatório** para o ElectrumX buscar transações.

### 1.4 Iniciar o daemon

```bash
InfiniteRicksd -daemon
```

Aguarde sincronização (pode levar horas/dias na primeira vez):

```bash
InfiniteRicksd getinfo
InfiniteRicksd getblockchaininfo
```

Confirme `"blocks"` subindo e `"verificationprogress"` próximo de `1`.

### 1.5 Serviço systemd (opcional)

```bash
sudo tee /etc/systemd/system/infinitericksd.service << 'EOF'
[Unit]
Description=InfiniteRicks full node
After=network.target

[Service]
Type=forking
User=root
ExecStart=/usr/local/bin/InfiniteRicksd -daemon -conf=/root/.InfiniteRicks/InfiniteRicks.conf
ExecStop=/usr/local/bin/InfiniteRicksd stop
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now infinitericksd
```

---

## Parte 2 — ElectrumX

Usamos [spesmilo/electrumx](https://github.com/spesmilo/electrumx) com uma classe de moeda customizada (Scrypt + transações com `nTime`, igual Peercoin/InfiniteRicks).

### 2.1 Dependências Python

```bash
sudo apt install -y python3 python3-pip python3-venv python3-dev \
  libleveldb-dev librocksdb-dev
```

### 2.2 Clonar e instalar

```bash
cd ~
git clone https://github.com/spesmilo/electrumx.git
cd electrumx
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip wheel
pip install -e .
```

### 2.3 Substituir `coins.py` (somente InfiniteRicks)

O ElectrumX oficial traz centenas de moedas. Use o arquivo **minimalista** deste repositório, que contém apenas InfiniteRicks:

```bash
cd ~/infinitericks-electrum
cp scripts/electrumx/coins.py ~/electrumx/src/electrumx/lib/coins.py
```

O arquivo inclui:
- Classe base `Coin` (infraestrutura ElectrumX)
- `ScryptMixin` (block hash Scrypt N=1024, r=1, p=1)
- `InfiniteRicks` (mainnet, RPC `31648`)
- `InfiniteRicksTestnet` (testnet, RPC `41648`, opcional)

**Parâmetros mainnet** (fonte: `docs/CHAIN_ANALYSIS.md`):

| Campo | Valor |
|-------|-------|
| P2PKH | `0x00` (endereços `1...`) |
| P2SH | `0x55` |
| RPC | `31648` |
| Genesis | `0000040917e53132256572dbcd3f780e94d40b4a1895672bfd64e0c5c0741dc8` |
| Block hash | Scrypt N=1024, r=1, p=1 (via `ScryptMixin`, version ≤ 6) |

### 2.4 Diretório de dados

```bash
sudo mkdir -p /var/lib/electrumx-infiniteRicks
sudo chown $USER:$USER /var/lib/electrumx-infiniteRicks
```

### 2.4 Configuração do ambiente

Crie `/etc/electrumx_infiniteRicks.conf`:

```bash
sudo tee /etc/electrumx_infiniteRicks.conf << 'EOF'
COIN=InfiniteRicks
NET=mainnet
DAEMON_URL=http://rick_rpc_user:TROQUE_POR_SENHA_FORTE_AQUI@127.0.0.1:31648/
DB_DIRECTORY=/var/lib/electrumx-infiniteRicks
BANNER=InfiniteRicks ElectrumX SPV

# TCP local + SSL público (ajuste conforme necessário)
SERVICES=tcp://127.0.0.1:50001,ssl://0.0.0.0:50002

# Performance
MAX_SESSIONS=500
CACHE_MB=500
PEER_DISCOVERY=off

# Certificado autoassinado (teste). Produção: use Let's Encrypt (Parte 3).
SSL_CERTFILE=/etc/electrumx/ssl/cert.pem
SSL_KEYFILE=/etc/electrumx/ssl/key.pem
EOF
```

Substitua `rick_rpc_user` e a senha pelos mesmos valores de `InfiniteRicks.conf`.

### 2.5 Certificado TLS (teste rápido)

A carteira usa TLS na porta `50002`. Para testes:

```bash
sudo mkdir -p /etc/electrumx/ssl
sudo openssl req -x509 -newkey rsa:4096 -keyout /etc/electrumx/ssl/key.pem \
  -out /etc/electrumx/ssl/cert.pem -days 3650 -nodes \
  -subj "/CN=electrum.infinitericks.local"
```

A carteira já aceita certificado autoassinado (`CERT_NONE`).

### 2.6 Serviço systemd

```bash
sudo tee /etc/systemd/system/electrumx-infiniteRicks.service << EOF
[Unit]
Description=ElectrumX for InfiniteRicks
After=network.target infinitericksd.service
Requires=infinitericksd.service

[Service]
EnvironmentFile=/etc/electrumx_infiniteRicks.conf
WorkingDirectory=$HOME/electrumx
ExecStart=$HOME/electrumx/.venv/bin/python -m electrumx_server
Restart=always
RestartSec=10
User=$USER

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now electrumx-infiniteRicks
```

### 2.7 Acompanhar indexação

```bash
sudo journalctl -u electrumx-infiniteRicks -f
```

Na primeira execução o ElectrumX **indexa toda a blockchain** — pode levar várias horas. Só aceita conexões de carteira quando terminar (ou parcialmente, conforme altura).

Verifique se a porta está escutando:

```bash
ss -tlnp | grep -E '50001|50002'
```

---

## Parte 3 — Firewall

```bash
# ElectrumX SPV (carteiras externas)
sudo ufw allow 50002/tcp comment 'ElectrumX SSL'

# P2P do nó (para sincronizar com a rede)
sudo ufw allow 31647/tcp comment 'InfiniteRicks P2P'

# NÃO exponha 31648 (RPC) na internet
sudo ufw enable
sudo ufw status
```

---

## Parte 4 — Testar

### 4.1 No servidor

```bash
cd ~/infinitericks-electrum
source .venv/bin/activate
python scripts/check_spv_server.py
```

Esperado:

```
[OK] 127.0.0.1:50002 (TLS)
        OK — server.version = [...]
```

Se testar localmente antes de TLS público, adicione temporariamente em `chainparams.py`:

```python
ELECTRUM_SERVERS = [
    ("127.0.0.1", 50001, False),  # TCP sem TLS, só nesta máquina
]
```

### 4.2 Teste manual JSON-RPC

```bash
python3 << 'PY'
import json, socket, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
s = ctx.wrap_socket(socket.create_connection(("127.0.0.1", 50002), 5), server_hostname="x")
s.sendall((json.dumps({"jsonrpc":"2.0","method":"server.version","params":["1.4","1.0"],"id":1})+"\n").encode())
print(s.recv(4096).decode())
PY
```

### 4.3 Apontar a carteira para seu servidor

Edite `infinitericks_wallet/config/chainparams.py`:

```python
ELECTRUM_SERVERS = [
    ("SEU_IP_PUBLICO", 50002, True),
]
```

Recompile o APK Android ou reinicie `python main.py` no desktop.

---

## Parte 5 — Produção com domínio (opcional)

Se tiver domínio (ex.: `electrum.seudominio.com`):

```bash
sudo apt install -y certbot
sudo certbot certonly --standalone -d electrum.seudominio.com
```

Atualize em `/etc/electrumx_infiniteRicks.conf`:

```ini
SSL_CERTFILE=/etc/letsencrypt/live/electrum.seudominio.com/fullchain.pem
SSL_KEYFILE=/etc/letsencrypt/live/electrum.seudominio.com/privkey.pem
```

E na carteira use o hostname em vez do IP.

---

## Solução de problemas

| Sintoma | Causa provável | Ação |
|---------|----------------|------|
| `Connection refused` :50002 | ElectrumX parado | `systemctl status electrumx-infiniteRicks` |
| ElectrumX reinicia em loop | RPC errado / daemon parado | Confira `DAEMON_URL` e `InfiniteRicksd getinfo` |
| `unknown coin InfiniteRicks` | Classe não adicionada | Verifique `coins.py` e `COIN=InfiniteRicks` |
| Carteira conecta, saldo 0 | Indexação incompleta | Aguarde `journalctl` mostrar altura atual |
| `txindex` missing | Daemon sem índice | Adicione `txindex=1`, reindexe o nó |
| Erro de compilação InfiniteRicksd | Código legado | Use Ubuntu 20.04 ou binário pré-compilado |

### Comandos úteis

```bash
# Nó
InfiniteRicksd getblockchaininfo
InfiniteRicksd getnetworkinfo

# ElectrumX
sudo systemctl restart electrumx-infiniteRicks
sudo journalctl -u electrumx-infiniteRicks -n 100 --no-pager

# Portas
ss -tlnp | grep -E '31648|50001|50002'
```

---

## Resumo rápido

```bash
# 1. Nó com txindex
InfiniteRicksd -daemon

# 2. ElectrumX com moeda InfiniteRicks em coins.py
systemctl start electrumx-infiniteRicks

# 3. Testar
python scripts/check_spv_server.py

# 4. Carteira apontando para SEU_IP:50002
python main.py
```

---

## Referências

- Parâmetros da rede: `docs/CHAIN_ANALYSIS.md`
- Cliente da carteira: `infinitericks_wallet/network/electrum_client.py`
- Snippet da moeda: `scripts/electrumx/coins.py` (substitui `src/electrumx/lib/coins.py`)
- ElectrumX docs: https://electrumx-spesmilo.readthedocs.io/
