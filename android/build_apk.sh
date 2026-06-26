#!/usr/bin/env bash
# Build InfiniteRicks Wallet APK using pyside6-android-deploy (official Qt tool).
#
# Requirements:
#   - Ubuntu 22.04+ (Linux host)
#   - Python 3.11 for APK build (official Qt wheels are cp311 only)
#   - JDK 17, Android SDK/NDK
#   - PySide6 + shiboken6 Android wheels (see setup_android_wheels below)
#
# Usage:
#   bash android/build_apk.sh              # full build
#   bash android/build_apk.sh --init       # generate pysidedeploy.spec only
#   bash android/build_apk.sh --setup-ndk  # download SDK/NDK into cache
#   bash android/build_apk.sh --download-wheels  # fetch PySide6/shiboken6 wheels
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SPEC_FILE="$SCRIPT_DIR/pysidedeploy.spec"
VENV="$PROJECT_ROOT/.venv-android"
CACHE_DIRS=("${HOME}/.pyside6_android_deploy" "${HOME}/.pyside6-android-deploy")
QT_WHEEL_BASE_PYSIDE="https://download.qt.io/official_releases/QtForPython/pyside6"
QT_WHEEL_BASE_SHIBOKEN="https://download.qt.io/official_releases/QtForPython/shiboken6"
PY_MIN=3.10
PY_MAX=3.11

resolve_android_python() {
    if [[ -n "${ANDROID_PYTHON:-}" ]]; then
        echo "$ANDROID_PYTHON"
        return 0
    fi
    if command -v python3.11 &>/dev/null; then
        echo python3.11
        return 0
    fi
    echo python3
}

ANDROID_PY="$(resolve_android_python)"

log() { echo "[build_apk] $*"; }
die() { echo "[build_apk] ERROR: $*" >&2; exit 1; }

detect_java_home() {
    if [[ -n "${JAVA_HOME:-}" && -x "${JAVA_HOME}/bin/java" ]]; then
        echo "$JAVA_HOME"
        return 0
    fi
    local candidate
    for candidate in /usr/lib/jvm/java-17-openjdk-* /usr/lib/jvm/java-11-openjdk-*; do
        [[ -x "$candidate/bin/java" ]] || continue
        echo "$candidate"
        return 0
    done
    if command -v java &>/dev/null; then
        local java_bin
        java_bin="$(readlink -f "$(command -v java)" 2>/dev/null || command -v java)"
        if [[ "$java_bin" == */bin/java ]]; then
            dirname "$(dirname "$java_bin")"
            return 0
        fi
    fi
    return 1
}

ensure_build_host_deps() {
    if ! command -v apt-get &>/dev/null; then
        return 0
    fi
    log "Checking Android cross-compile host dependencies..."
    dpkg --add-architecture i386 2>/dev/null || true
    local packages=(
        build-essential git zip unzip autoconf automake libtool
        pkg-config zlib1g-dev libffi-dev libssl-dev cmake
        libc6-dev-i386 lib32z1-dev
    )
    if [[ "$(id -u)" -eq 0 ]]; then
        apt-get update -qq
        DEBIAN_FRONTEND=noninteractive apt-get install -y "${packages[@]}" || true
    elif command -v sudo &>/dev/null; then
        sudo apt-get update -qq
        DEBIAN_FRONTEND=noninteractive sudo apt-get install -y "${packages[@]}" || true
    fi
}

ensure_java() {
    local java_home
    if java_home="$(detect_java_home)"; then
        export JAVA_HOME="$java_home"
        export PATH="$JAVA_HOME/bin:$PATH"
        log "Using JAVA_HOME=$JAVA_HOME ($(java -version 2>&1 | head -1))"
        return 0
    fi

    log "JDK not found — installing openjdk-17-jdk (required by sdkmanager)..."
    if command -v apt-get &>/dev/null; then
        if [[ "$(id -u)" -eq 0 ]]; then
            apt-get update -qq
            DEBIAN_FRONTEND=noninteractive apt-get install -y openjdk-17-jdk
        elif command -v sudo &>/dev/null; then
            sudo apt-get update -qq
            DEBIAN_FRONTEND=noninteractive sudo apt-get install -y openjdk-17-jdk
        else
            die "JDK 17 required. Install: apt install openjdk-17-jdk"
        fi
        java_home="$(detect_java_home)" || die "JDK install failed"
        export JAVA_HOME="$java_home"
        export PATH="$JAVA_HOME/bin:$PATH"
        log "Installed JAVA_HOME=$JAVA_HOME"
        return 0
    fi

    die "JDK 17 required for sdkmanager. Install openjdk-17-jdk and export JAVA_HOME."
}

sdk_is_complete() {
    local sdk_dir="$1"
    [[ -d "$sdk_dir/platform-tools" ]] \
        && [[ -d "$sdk_dir/platforms" ]] \
        && [[ -n "$(find "$sdk_dir/platforms" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | head -1)" ]]
}

resolve_ndk_root() {
    local path="$1" nested
    [[ -n "$path" ]] || return 1
    if [[ -x "$path/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readobj" ]]; then
        echo "$path"
        return 0
    fi
    for nested in "$path"/android-ndk-*; do
        [[ -d "$nested" ]] || continue
        if [[ -x "$nested/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readobj" ]]; then
            echo "$nested"
            return 0
        fi
    done
    return 1
}

find_valid_ndk() {
    local cache candidate resolved
    for cache in "${CACHE_DIRS[@]}"; do
        while IFS= read -r candidate; do
            if resolved="$(resolve_ndk_root "$candidate")"; then
                echo "$resolved"
                return 0
            fi
        done < <(find "$cache" -type d -name 'android-ndk*' 2>/dev/null)
    done
    return 1
}

ndk_cache_ready() {
    local cache="$1"
    resolve_ndk_root "$cache/android-ndk" &>/dev/null
}

check_python() {
    local ver
    ver="$("$ANDROID_PY" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    log "Python version: $ver ($ANDROID_PY)"
    "$ANDROID_PY" - <<'PY' || die "Python 3.10 or 3.11 required (buildozer breaks on 3.12+)"
import sys
v = sys.version_info
if not ((3, 10) <= (v.major, v.minor) <= (3, 11)):
    raise SystemExit(1)
PY
}

check_python_apk() {
    local ver
    ver="$("$ANDROID_PY" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    if [[ "$ver" != "3.11" ]]; then
        die "Android APK build requires Python 3.11 (official Qt wheels are cp311 only). Install: apt install python3.11 python3.11-venv && ANDROID_PYTHON=python3.11 bash android/build_apk.sh"
    fi
}

setup_venv() {
    local wanted_ver
    wanted_ver="$("$ANDROID_PY" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    if [[ -d "$VENV" && -x "$VENV/bin/python" ]]; then
        local venv_ver
        venv_ver="$("$VENV/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
        if [[ "$venv_ver" != "$wanted_ver" ]]; then
            log "Recreating Android venv (Python $venv_ver -> $wanted_ver)"
            rm -rf "$VENV"
        fi
    fi
    if [[ ! -d "$VENV" ]]; then
        log "Creating Android build venv at $VENV"
        "$ANDROID_PY" -m venv "$VENV"
    fi
    # shellcheck disable=SC1091
    source "$VENV/bin/activate"
    pip install -q --upgrade pip
    pip install -q pyside6 buildozer cython
    install_android_deploy_deps
    pip install -q -r "$PROJECT_ROOT/requirements.txt" || true
}

install_android_deploy_deps() {
    local req_file
    req_file="$(python -c 'import PySide6, pathlib; print(pathlib.Path(PySide6.__file__).parent / "scripts" / "requirements-android.txt")' 2>/dev/null || true)"
    if [[ -n "$req_file" && -f "$req_file" ]]; then
        log "Installing pyside6-android-deploy dependencies..."
        pip install -q -r "$req_file"
        return 0
    fi
    log "Installing pyside6-android-deploy dependencies (fallback list)..."
    pip install -q jinja2 pkginfo tqdm "packaging==24.1"
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

latest_qt_android_wheel() {
    local base="$1" prefix="$2"
    curl -fsSL "${base}/" | grep -oE "${prefix}-[0-9.]+-[0-9.]+-cp311-cp311-android_aarch64\.whl" | sort -V | tail -1
}

matching_qt_android_wheel() {
    local base="$1" prefix="$2" version="$3"
    curl -fsSL "${base}/" | grep -oE "${prefix}-${version}-[^\"]+-cp311-cp311-android_aarch64\.whl" | head -1
}

download_file_if_missing() {
    local url="$1" dest="$2" label="$3"
    if [[ -f "$dest" ]]; then
        log "Already have $(basename "$dest")"
        return 0
    fi
    log "Downloading $label (~80MB)..."
    curl -fL --progress-bar -o "$dest" "$url"
}

download_wheels_official() {
    local wheels_dir="$PROJECT_ROOT/android/wheels"
    local ver="${PYSIDE_ANDROID_VERSION:-}"
    local pyside_file shiboken_file pyside_ver

    mkdir -p "$wheels_dir"
    log "Fetching PySide6 Android wheel list from Qt CDN..."

    if [[ -n "$ver" ]]; then
        pyside_file="$(matching_qt_android_wheel "$QT_WHEEL_BASE_PYSIDE" "PySide6" "$ver")"
        shiboken_file="$(matching_qt_android_wheel "$QT_WHEEL_BASE_SHIBOKEN" "shiboken6" "$ver")"
    else
        pyside_file="$(latest_qt_android_wheel "$QT_WHEEL_BASE_PYSIDE" "PySide6")"
        pyside_ver="$(echo "$pyside_file" | sed -E 's/^PySide6-([0-9.]+)-.*/\1/')"
        shiboken_file="$(matching_qt_android_wheel "$QT_WHEEL_BASE_SHIBOKEN" "shiboken6" "$pyside_ver")"
    fi

    [[ -n "$pyside_file" && -n "$shiboken_file" ]] || die "Could not find cp311 android_aarch64 wheels on Qt CDN"

    log "PySide6 wheel: $pyside_file"
    log "Shiboken6 wheel: $shiboken_file"
    download_file_if_missing "$QT_WHEEL_BASE_PYSIDE/$pyside_file" "$wheels_dir/$pyside_file" "$pyside_file"
    download_file_if_missing "$QT_WHEEL_BASE_SHIBOKEN/$shiboken_file" "$wheels_dir/$shiboken_file" "$shiboken_file"
}

download_wheels_if_missing() {
    find_wheels
    if [[ -n "${PYSIDE_WHEEL:-}" && -n "${SHIBOKEN_WHEEL:-}" ]]; then
        return 0
    fi
    download_wheels_qtpip
    find_wheels
    if [[ -n "${PYSIDE_WHEEL:-}" && -n "${SHIBOKEN_WHEEL:-}" ]]; then
        return 0
    fi
    download_wheels_official
    find_wheels
}

setup_ndk_sdk() {
    local cache sdk_dir
    for cache in "${CACHE_DIRS[@]}"; do
        sdk_dir="$cache/android-sdk"
        if ndk_cache_ready "$cache" && [[ -d "$sdk_dir" ]] && sdk_is_complete "$sdk_dir"; then
            log "Using cached NDK/SDK under $cache"
            return 0
        fi
    done

    ensure_java
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
    local cache resolved

    if [[ -n "$NDK_PATH" ]]; then
        resolved="$(resolve_ndk_root "$NDK_PATH" || true)"
        [[ -n "$resolved" ]] || die "Invalid NDK_PATH (missing llvm-readobj): $NDK_PATH"
        NDK_PATH="$resolved"
    else
        NDK_PATH="$(find_valid_ndk || true)"
    fi

    if [[ -z "$SDK_PATH" ]]; then
        for cache in "${CACHE_DIRS[@]}"; do
            SDK_PATH="$(find "$cache" -maxdepth 2 -type d -name 'android-sdk*' 2>/dev/null | head -1)"
            [[ -n "$SDK_PATH" ]] && break
        done
    fi
    export ANDROID_NDK_HOME="${NDK_PATH:-}"
    export ANDROID_SDK_ROOT="${SDK_PATH:-}"
    fix_android_sdk_layout "${SDK_PATH:-}"
}

fix_android_sdk_layout() {
    local sdk="$1"
    local legacy_bin cmdline_bin
    [[ -n "$sdk" && -d "$sdk" ]] || return 0
    legacy_bin="$sdk/tools/bin"
    cmdline_bin="$sdk/cmdline-tools/bin"
    if [[ ! -x "$cmdline_bin/sdkmanager" ]]; then
        log "WARNING: sdkmanager not found at $cmdline_bin/sdkmanager"
        return 0
    fi
    mkdir -p "$legacy_bin"
    ln -sfn "$cmdline_bin/sdkmanager" "$legacy_bin/sdkmanager"
    [[ -x "$cmdline_bin/avdmanager" ]] && ln -sfn "$cmdline_bin/avdmanager" "$legacy_bin/avdmanager"
    log "Linked buildozer sdkmanager -> $legacy_bin/sdkmanager"
}

run_android_deploy() {
    [[ -n "${PYSIDE_WHEEL:-}" ]] || die "PYSIDE_WHEEL not set"
    [[ -n "${SHIBOKEN_WHEEL:-}" ]] || die "SHIBOKEN_WHEEL not set"

    if ! python -c "import PySide6" &>/dev/null; then
        die "PySide6 not found in Android venv"
    fi

    cd "$PROJECT_ROOT"
    log "Running Android deploy (with wallet buildozer requirements)..."
    python "$SCRIPT_DIR/deploy_wallet.py" \
        --name "infinitericks_wallet" \
        --config-file "$SPEC_FILE" \
        --force \
        --verbose \
        --wheel-pyside "$PYSIDE_WHEEL" \
        --wheel-shiboken "$SHIBOKEN_WHEEL" \
        --extra-ignore-dirs ".venv-android,.venv,android/wheels,tests,.git" \
        --extra-modules "Network" \
        --keep-deployment-files \
        ${NDK_PATH:+--ndk-path "$NDK_PATH"} \
        ${SDK_PATH:+--sdk-path "$SDK_PATH"} \
        "$@"
}

print_wheel_help() {
    cat <<'EOF'

Android wheels not found. The script can download them automatically:

  bash android/build_apk.sh --download-wheels

Or download manually (requires Python 3.11 wheels, cp311):

  mkdir -p android/wheels
  curl -LO https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.10.3-6.10.3-cp311-cp311-android_aarch64.whl
  curl -LO https://download.qt.io/official_releases/QtForPython/shiboken6/shiboken6-6.10.3-6.10.3-cp311-cp311-android_aarch64.whl
  mv PySide6-*.whl shiboken6-*.whl android/wheels/

APK build requires Python 3.11:
  apt install python3.11 python3.11-venv
  ANDROID_PYTHON=python3.11 bash android/build_apk.sh

EOF
}

main() {
    log "=== InfiniteRicks Wallet Android Build ==="
    check_python
    setup_venv
    ensure_java

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
        --download-wheels)
            download_wheels_official
            find_wheels
            log "PySide wheel: ${PYSIDE_WHEEL:-not found}"
            log "Shiboken wheel: ${SHIBOKEN_WHEEL:-not found}"
            exit 0
            ;;
        --help|-h)
            head -20 "$0"
            exit 0
            ;;
    esac

    setup_ndk_sdk
    find_ndk_sdk
    check_python_apk
    ensure_build_host_deps
    download_wheels_if_missing

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
