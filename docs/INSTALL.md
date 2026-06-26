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

### Passo 1: Python 3.10 ou 3.11

```bash
python3.10 --version   # deve ser 3.10.x ou 3.11.x
```

### Passo 2: NDK e SDK (primeira vez)

```bash
bash android/build_apk.sh --setup-ndk
```

Isso baixa o NDK/SDK para `~/.pyside6_android_deploy` (ou `~/.pyside6-android-deploy`).

### Passo 3: Wheels Android PySide6

Coloque os wheels em `android/wheels/`:

```bash
pip install qtpip
qtpip download PySide6 --android --arch aarch64 -d android/wheels
qtpip download shiboken6 --android --arch aarch64 -d android/wheels
```

Alternativa: baixe de [Qt for Python releases](https://download.qt.io/official_releases/QtForPython/).

### Passo 4: Compilar APK

```bash
bash android/build_apk.sh
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
| Wheels Android ausentes | Baixe PySide6/shiboken6 `android_aarch64` em `android/wheels/` |
| `No Connection` | Verifique internet e firewall na porta 50002 |
| Senha incorreta | Use a senha definida na criação |
| Seed inválida | Confirme 12 palavras BIP39 em inglês |
