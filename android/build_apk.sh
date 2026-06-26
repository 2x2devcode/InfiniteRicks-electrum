#!/usr/bin/env bash
# Build Android APK using PySide6-Deploy (Qt for Python official tool)
# Requires: Ubuntu 22.04+, Python 3.10+, Android SDK, NDK, JDK 17
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build/android"
VENV="$PROJECT_ROOT/.venv"

echo "=== InfiniteRicks Wallet Android Build ==="

python3 -m venv "$VENV" 2>/dev/null || true
source "$VENV/bin/activate"
pip install -q -r "$PROJECT_ROOT/requirements.txt"
pip install -q pyside6

# Install pyside6-deploy if available
pip install -q pyside6-essentials 2>/dev/null || true

export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}"
export ANDROID_NDK_ROOT="${ANDROID_NDK_ROOT:-$ANDROID_SDK_ROOT/ndk/25.2.9519653}"

mkdir -p "$BUILD_DIR"

cat > "$BUILD_DIR/pysidedeploy.spec" << 'SPEC'
[app]

title = InfiniteRicks Wallet
project_dir = .
input_file = main.py
exec_directory = .
icon = resources/icons/app_icon.png

[android]

packages = PySide6,shiboken6,coincurve,mnemonic,argon2,cryptography,qrcode,PIL,scrypt
ndk_path = ${ANDROID_NDK_ROOT}
sdk_path = ${ANDROID_SDK_ROOT}
arch = arm64-v8a
min_sdk = 24
target_sdk = 35
permissions = INTERNET,CAMERA
SPEC

echo "Running pyside6-deploy for Android..."
if command -v pyside6-deploy &>/dev/null; then
    cd "$PROJECT_ROOT"
    pyside6-deploy --config "$BUILD_DIR/pysidedeploy.spec" --android-platform android-35
    echo "APK built successfully."
else
    echo "pyside6-deploy not found. Install Qt for Python deployment tools."
    echo "Alternative: use buildozer (see android/buildozer.spec)"
    exit 1
fi
