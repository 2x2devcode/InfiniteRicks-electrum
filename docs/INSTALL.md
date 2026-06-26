# Manual de Instalação

## Requisitos

### Desktop (Linux/macOS/Windows)
- Python 3.10+
- pip

### Android (compilação)
- Ubuntu 22.04
- Python 3.10+
- Android SDK API 35
- Android NDK 25+
- JDK 17

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

### Opção 1: PySide6-Deploy (recomendado)

```bash
export ANDROID_SDK_ROOT=$HOME/Android/Sdk
export ANDROID_NDK_ROOT=$ANDROID_SDK_ROOT/ndk/25.2.9519653
bash android/build_apk.sh
```

### Opção 2: Buildozer

```bash
pip install buildozer cython
cd android
buildozer android debug
```

O APK será gerado em `bin/` ou `build/android/`.

## Servidor SPV

A carteira conecta por padrão a:
- Host: `144.91.107.244`
- Porta: `50002` (TLS)

Servidores adicionais podem ser configurados em `infinitericks_wallet/config/chainparams.py`.

## Solução de problemas

| Problema | Solução |
|----------|---------|
| `No Connection` | Verifique internet e firewall na porta 50002 |
| Senha incorreta | Use a senha definida na criação |
| Seed inválida | Confirme 12 palavras BIP39 em inglês |
