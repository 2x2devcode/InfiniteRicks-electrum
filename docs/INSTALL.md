# Manual de Instalação

## Requisitos

### Desktop (Linux/macOS/Windows)
- Python 3.10+
- pip

### Android (compilação)
- Ubuntu 22.04 (host Linux)
- **Python 3.10 ou 3.11** (buildozer não suporta 3.12+)
- JDK 17
- Android SDK + NDK (baixados automaticamente pelo script ou manualmente)
- Wheels PySide6 + shiboken6 para `android_aarch64`

## Instalação Desktop

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Primeira execução

1. Escolha **Criar Carteira** ou **Importar Carteira**
2. Anote as 12 palavras (criar) ou digite sua seed (importar)
3. Defina uma senha forte (mínimo 8 caracteres)
4. A carteira sincroniza automaticamente com o servidor SPV

## Build APK Android

Use `pyside6-android-deploy` (ferramenta oficial Qt). **Não** use `pyside6-deploy --android-platform` — esse argumento não existe.

### Passo 1: Python 3.11 (obrigatório para APK)

Os wheels oficiais do Qt são **cp311** apenas. Python 3.10 serve para testes desktop, mas o APK exige 3.11:

```bash
apt install -y python3.11 python3.11-venv
python3.11 --version
export ANDROID_PYTHON=python3.11
```

### Passo 2: JDK 17

O `sdkmanager` exige Java. No Ubuntu:

```bash
sudo apt update
sudo apt install -y openjdk-17-jdk
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
```

O script `build_apk.sh` tenta instalar automaticamente se o JDK não estiver presente.

### Passo 3: NDK e SDK (primeira vez)

```bash
bash android/build_apk.sh --setup-ndk
```

Isso baixa o NDK/SDK para `~/.pyside6_android_deploy` (ou `~/.pyside6-android-deploy`).

### Passo 4: Wheels Android PySide6

O script baixa automaticamente do CDN oficial do Qt. Também pode rodar só o download:

```bash
bash android/build_apk.sh --download-wheels
```

Isso salva em `android/wheels/` (~160MB total). Versão específica:

```bash
PYSIDE_ANDROID_VERSION=6.10.3 bash android/build_apk.sh --download-wheels
```

Manual (alternativa):

```bash
mkdir -p android/wheels
curl -fL -o android/wheels/PySide6-6.10.3-6.10.3-cp311-cp311-android_aarch64.whl \
  https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.10.3-6.10.3-cp311-cp311-android_aarch64.whl
curl -fL -o android/wheels/shiboken6-6.10.3-6.10.3-cp311-cp311-android_aarch64.whl \
  https://download.qt.io/official_releases/QtForPython/shiboken6/shiboken6-6.10.3-6.10.3-cp311-cp311-android_aarch64.whl
```

### Passo 5: Compilar APK

O script detecta e remove automaticamente cache antiga (nome com espaços, Python sem pin).
Para limpeza completa manual:

```bash
rm -rf .buildozer buildozer.spec deployment
# ou:
bash android/build_apk.sh --clean
```

```bash
ANDROID_PYTHON=python3.11 bash android/build_apk.sh
```

O script usa `pyside6-android-deploy` com `android/pysidedeploy.spec`. O APK de debug aparece no diretório do projeto ou em `deployment/`.

Variáveis opcionais:

```bash
export PYSIDE_WHEEL=android/wheels/PySide6-....whl
export SHIBOKEN_WHEEL=android/wheels/shiboken6-....whl
export NDK_PATH=...
export SDK_PATH=...
bash android/build_apk.sh
```

## Servidor SPV

A carteira conecta por padrão a:
- Host: `144.91.107.244`
- Porta: `50002` (TLS)

Servidores adicionais podem ser configurados em `infinitericks_wallet/config/chainparams.py`.

## Solução de problemas

| Problema | Solução |
|----------|---------|
| `unrecognized arguments: --android-platform` | Use `bash android/build_apk.sh` (chama `pyside6-android-deploy`, não `pyside6-deploy`) |
| `Python 3.12+` / buildozer | Use Python 3.10 ou 3.11 para compilar o APK |
| `No module named 'git'` | Rode `bash android/build_apk.sh` de novo — o script instala `gitpython` antes do download do NDK |
| `Java Runtime not found` | Instale JDK 17: `apt install openjdk-17-jdk` (o script tenta instalar sozinho) |
| `C compiler cannot create executables` | Rode `git pull`, instale deps: `apt install build-essential libc6-dev-i386 lib32z1-dev zlib1g-dev`, limpe `rm -rf .buildozer buildozer.spec deployment` e tente de novo |
| `dist_name` com espaços | O nome interno do pacote não pode ter espaços — use `infinitericks_wallet` |
| Python 3.10 no build APK | Use Python 3.11: `ANDROID_PYTHON=python3.11 bash android/build_apk.sh` |
| `No Connection` | Verifique internet e firewall na porta 50002 |
| Senha incorreta | Use a senha definida na criação |
| Seed inválida | Confirme 12 palavras BIP39 em inglês |
