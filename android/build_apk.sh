#!/usr/bin/env bash
# Build InfiniteRicks Wallet APK using pyside6-android-deploy (official Qt tool).
#
# Requirements:
#   - Ubuntu 22.04+ (Linux host)
#   - Python 3.10 or 3.11 (buildozer does NOT support 3.12+)
#   - JDK 17, Android SDK/NDK
#   - PySide6 + shiboken6 Android wheels (see setup_android_wheels below)
#
# Usage:
#   bash android/build_apk.sh              # full build
#   bash android/build_apk.sh --init       # generate pysidedeploy.spec only
#   bash android/build_apk.sh --setup-ndk  # download SDK/NDK into cache
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SPEC_FILE="$SCRIPT_DIR/pysidedeploy.spec"
VENV="$PROJECT_ROOT/.venv-android"
CACHE_DIRS=("${HOME}/.pyside6_android_deploy" "${HOME}/.pyside6-android-deploy")
PY_MIN=3.10
PY_MAX=3.11

log() { echo "[build_apk] $*"; }
die() { echo "[build_apk] ERROR: $*" >&2; exit 1; }

check_python() {
    local ver
    ver="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    log "Python version: $ver"
    python3 - <<'PY' || die "Python 3.10 or 3.11 required (buildozer breaks on 3.12+)"
import sys
v = sys.version_info
if not ((3, 10) <= (v.major, v.minor) <= (3, 11)):
    raise SystemExit(1)
PY
}

setup_venv() {
    if [[ ! -d "$VENV" ]]; then
        log "Creating Android build venv at $VENV"
        python3 -m venv "$VENV"
    fi
    # shellcheck disable=SC1091
    source "$VENV/bin/activate"
    pip install -q --upgrade pip
    pip install -q pyside6 buildozer cython
    pip install -q -r "$PROJECT_ROOT/requirements.txt" || true
}

find_wheels() {
  PYSIDE_WHEEL="${PYSIDE_WHEEL:-}"
  SHIBOKEN_WHEEL="${SHIBOKEN_WHEEL:-}"

  if [[ -z "$PYSIDE_WHEEL" || -z "$SHIBOKEN_WHEEL" ]]; then
    local cache
    for cache in "${CACHE_DIRS[@]}"; do
      for dir in "$PROJECT_ROOT/android/wheels" "$cache/wheels" "$HOME/Downloads"; do
      [[ -d "$dir" ]] || continue
        PYSIDE_WHEEL="${PYSIDE_WHEEL:-$(find "$dir" -maxdepth 1 -name 'PySide6-*-android_aarch64.whl' 2>/dev/null | head -1)}"
        SHIBOKEN_WHEEL="${SHIBOKEN_WHEEL:-$(find "$dir" -maxdepth 1 -name 'shiboken6-*-android_aarch64.whl' 2>/dev/null | head -1)}"
      done
    done
  fi
}

download_wheels_qtpip() {
    if command -v qtpip &>/dev/null; then
        log "Downloading Android wheels via qtpip..."
        mkdir -p "$PROJECT_ROOT/android/wheels"
        qtpip download PySide6 --android --arch aarch64 -d "$PROJECT_ROOT/android/wheels" || true
        qtpip download shiboken6 --android --arch aarch64 -d "$PROJECT_ROOT/android/wheels" || true
    fi
}

setup_ndk_sdk() {
    local cache
    for cache in "${CACHE_DIRS[@]}"; do
        if find "$cache" -maxdepth 3 -type d -name 'android-ndk*' 2>/dev/null | grep -q .; then
            log "Using cached NDK/SDK under $cache"
            return 0
        fi
    done
    log "Downloading Android NDK/SDK (first time only, ~1GB)..."
    local tmp
    tmp="$(mktemp -d)"
    git clone --depth 1 https://code.qt.io/pyside/pyside-setup.git "$tmp/pyside-setup" 2>/dev/null || \
        git clone --depth 1 https://github.com/qt/pyside-setup.git "$tmp/pyside-setup"
    log "Installing NDK downloader dependencies (gitpython, jinja2, tqdm)..."
    pip install -q -r "$tmp/pyside-setup/tools/cross_compile_android/requirements.txt"
    python "$tmp/pyside-setup/tools/cross_compile_android/main.py" \
        --download-only --skip-update --auto-accept-license
    rm -rf "$tmp"
}

find_ndk_sdk() {
    NDK_PATH="${NDK_PATH:-}"
    SDK_PATH="${SDK_PATH:-}"
    local cache
    if [[ -z "$NDK_PATH" ]]; then
        for cache in "${CACHE_DIRS[@]}"; do
            NDK_PATH="$(find "$cache" -maxdepth 3 -type d -name 'android-ndk*' 2>/dev/null | head -1)"
            [[ -n "$NDK_PATH" ]] && break
        done
    fi
    if [[ -z "$SDK_PATH" ]]; then
        for cache in "${CACHE_DIRS[@]}"; do
            SDK_PATH="$(find "$cache" -maxdepth 2 -type d -name 'android-sdk*' 2>/dev/null | head -1)"
            [[ -n "$SDK_PATH" ]] && break
        done
    fi
    export ANDROID_NDK_HOME="${NDK_PATH:-}"
    export ANDROID_SDK_ROOT="${SDK_PATH:-}"
}

run_android_deploy() {
    local extra_args=()
    [[ -n "${PYSIDE_WHEEL:-}" ]] && extra_args+=(--wheel-pyside="$PYSIDE_WHEEL")
    [[ -n "${SHIBOKEN_WHEEL:-}" ]] && extra_args+=(--wheel-shiboken="$SHIBOKEN_WHEEL")
    [[ -n "${NDK_PATH:-}" ]] && extra_args+=(--ndk-path="$NDK_PATH")
    [[ -n "${SDK_PATH:-}" ]] && extra_args+=(--sdk-path="$SDK_PATH")

    if ! command -v pyside6-android-deploy &>/dev/null; then
        die "pyside6-android-deploy not found. Install: pip install pyside6"
    fi

    cd "$PROJECT_ROOT"
    log "Running pyside6-android-deploy..."
    pyside6-android-deploy \
        --name "InfiniteRicks Wallet" \
        --config-file "$SPEC_FILE" \
        --force \
        --verbose \
        "${extra_args[@]}" \
        "$@"
}

print_wheel_help() {
    cat <<'EOF'

Android wheels not found. Download PySide6 Android wheels:

  Option A — qtpip (if Qt account configured):
    pip install qtpip
    qtpip download PySide6 --android --arch aarch64 -d android/wheels
    qtpip download shiboken6 --android --arch aarch64 -d android/wheels

  Option B — Qt downloads page:
    https://download.qt.io/official_releases/QtForPython/
    Place PySide6-*-android_aarch64.whl and shiboken6-*-android_aarch64.whl
    into android/wheels/

  Option C — cross-compile (advanced):
    See docs/INSTALL.md section "Build Android APK"

Then set:
  export PYSIDE_WHEEL=android/wheels/PySide6-....whl
  export SHIBOKEN_WHEEL=android/wheels/shiboken6-....whl
  bash android/build_apk.sh

EOF
}

main() {
    log "=== InfiniteRicks Wallet Android Build ==="
    check_python
    setup_venv

    case "${1:-}" in
        --init)
            run_android_deploy --init
            log "Created/updated $SPEC_FILE"
            exit 0
            ;;
        --setup-ndk)
            setup_ndk_sdk
            find_ndk_sdk
            log "NDK: ${NDK_PATH:-not found}"
            log "SDK: ${SDK_PATH:-not found}"
            exit 0
            ;;
        --help|-h)
            head -20 "$0"
            exit 0
            ;;
    esac

    setup_ndk_sdk
    find_ndk_sdk
    download_wheels_qtpip
    find_wheels

    if [[ -z "${PYSIDE_WHEEL:-}" || -z "${SHIBOKEN_WHEEL:-}" ]]; then
        print_wheel_help
        die "Missing PySide6/shiboken6 Android wheels"
    fi

    log "PySide wheel: $PYSIDE_WHEEL"
    log "Shiboken wheel: $SHIBOKEN_WHEEL"
    log "NDK: ${NDK_PATH:-auto}"
    log "SDK: ${SDK_PATH:-auto}"

    run_android_deploy

    log "Build finished. Look for *.apk in $PROJECT_ROOT"
    find "$PROJECT_ROOT" -maxdepth 3 -name '*.apk' -printf '  %p\n' 2>/dev/null || true
}

main "$@"
