#!/usr/bin/env python3
"""Android deploy wrapper: write buildozer.spec and purge stale p4a cache before build."""

from __future__ import annotations

import argparse
import logging
import re
import shutil
import sys
import traceback
from configparser import ConfigParser
from pathlib import Path

import PySide6

sys.path.insert(0, str(Path(PySide6.__file__).resolve().parent / "scripts"))

from deploy_lib import cleanup, PythonExecutable
from deploy_lib.android import AndroidData, AndroidConfig
from deploy_lib.android.buildozer import Buildozer

WALLET_REQUIREMENTS = (
    "coincurve",
    "mnemonic",
    "argon2-cffi",
    "cryptography",
    "qrcode",
    "pillow",
    "scrypt",
    "openssl",
)

ANDROID_PYTHON_VERSION = "3.11.9"
ANDROID_PACKAGE_NAME = "infinitericks_wallet"
ANDROID_PACKAGE_DOMAIN = "com.infinitericks"
PYTHON_REQUIREMENT = f"python3=={ANDROID_PYTHON_VERSION}"


def _read_buildozer_spec(project_dir: Path) -> ConfigParser | None:
    spec = project_dir / "buildozer.spec"
    if not spec.exists():
        return None
    parser = ConfigParser(comment_prefixes="#", allow_no_value=True)
    parser.read(spec)
    return parser


def spec_needs_refresh(project_dir: Path) -> bool:
    parser = _read_buildozer_spec(project_dir)
    if parser is None or not parser.has_section("app"):
        return True

    package_name = parser.get("app", "package.name", fallback="")
    requirements = parser.get("app", "requirements", fallback="").replace(" ", "")
    if package_name != ANDROID_PACKAGE_NAME or " " in package_name:
        return True
    if PYTHON_REQUIREMENT not in requirements:
        return True
    return False


def buildozer_cache_is_stale(project_dir: Path) -> bool:
    buildozer_dir = project_dir / ".buildozer"
    if not buildozer_dir.exists():
        return False

    if spec_needs_refresh(project_dir):
        return True

    stale_name_pattern = re.compile(r"InfiniteRicks\s+Wallet", re.IGNORECASE)
    for path in buildozer_dir.rglob("*"):
        if stale_name_pattern.search(path.name) or " " in path.name:
            return True

    platform_dir = buildozer_dir / "android" / "platform"
    if platform_dir.exists():
        for dist_dir in platform_dir.glob("build-*/dists/*"):
            if dist_dir.name != ANDROID_PACKAGE_NAME:
                return True

    return False


def purge_stale_android_cache(project_dir: Path, *, force: bool = False) -> bool:
    """Remove cached native builds when package name or Python version is wrong."""
    if not force and not buildozer_cache_is_stale(project_dir):
        return False

    removed: list[str] = []
    for rel in (".buildozer", "buildozer.spec"):
        target = project_dir / rel
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            removed.append(rel)

    if removed:
        logging.warning(
            "[deploy_wallet] Purged stale Android cache (%s). "
            "Spaces in dist_name break the NDK compiler.",
            ", ".join(removed),
        )
    return bool(removed)


def patch_buildozer_spec(project_dir: Path, config: AndroidConfig) -> None:
    spec = project_dir / "buildozer.spec"
    if not spec.exists():
        raise RuntimeError(f"buildozer.spec missing in {project_dir}")

    parser = ConfigParser(comment_prefixes="#", allow_no_value=True)
    parser.read(spec)
    if not parser.has_section("app"):
        raise RuntimeError("buildozer.spec has no [app] section")

    requirements = [
        PYTHON_REQUIREMENT,
        "shiboken6",
        "PySide6",
        *WALLET_REQUIREMENTS,
    ]
    parser.set("app", "requirements", ",".join(requirements))
    parser.set("app", "package.name", ANDROID_PACKAGE_NAME)
    parser.set("app", "package.domain", ANDROID_PACKAGE_DOMAIN)
    parser.set("app", "title", ANDROID_PACKAGE_NAME)
    parser.set("app", "android.api", "33")
    parser.set("app", "android.minapi", "24")
    parser.set("app", "android.accept_sdk_license", "True")
    parser.set("app", "android.archs", config.arch)

    if config.ndk_path:
        parser.set("app", "android.ndk_path", str(config.ndk_path))
    if config.sdk_path:
        parser.set("app", "android.sdk_path", str(config.sdk_path))

    if not parser.has_section("buildozer"):
        parser.add_section("buildozer")
    parser.set("buildozer", "warn_on_root", "0")
    parser.set("buildozer", "log_level", "2")

    with spec.open("w", encoding="utf-8") as handle:
        parser.write(handle)

    verify_buildozer_spec(project_dir)
    logging.info(
        "[deploy_wallet] Wrote buildozer.spec (python %s, package %s)",
        ANDROID_PYTHON_VERSION,
        ANDROID_PACKAGE_NAME,
    )


def verify_buildozer_spec(project_dir: Path) -> None:
    parser = _read_buildozer_spec(project_dir)
    if parser is None:
        raise RuntimeError("buildozer.spec was not created")

    package_name = parser.get("app", "package.name", fallback="")
    requirements = parser.get("app", "requirements", fallback="")
    if package_name != ANDROID_PACKAGE_NAME or " " in package_name:
        raise RuntimeError(
            f"Invalid package.name '{package_name}' — must be '{ANDROID_PACKAGE_NAME}' "
            "with no spaces (spaces break NDK cross-compile paths)"
        )
    if PYTHON_REQUIREMENT not in requirements.replace(" ", ""):
        raise RuntimeError(
            f"buildozer.spec must pin {PYTHON_REQUIREMENT}, got: {requirements}"
        )


def write_buildozer_spec(config: AndroidConfig, project_dir: Path) -> None:
    """Always regenerate buildozer.spec; PySide skips init when the file already exists."""
    spec = project_dir / "buildozer.spec"
    if spec.exists():
        spec.unlink()
        logging.info("[deploy_wallet] Removed existing buildozer.spec for regeneration")

    Buildozer.initialize(pysidedeploy_config=config)
    patch_buildozer_spec(project_dir, config)


def deploy(
    name: str | None,
    pyside_wheel: Path,
    shiboken_wheel: Path,
    ndk_path: Path | None,
    sdk_path: Path | None,
    config_file: Path,
    init: bool,
    loglevel: int,
    dry_run: bool,
    force: bool,
    extra_ignore_dirs: str | None,
    extra_modules: str | None,
    keep_deployment_files: bool = True,
    clean_cache: bool = False,
) -> int:
    logging.basicConfig(level=loglevel)

    package_name = ANDROID_PACKAGE_NAME
    if name and name.replace("_", "").lower() != package_name.replace("_", "").lower():
        logging.warning(
            "[deploy_wallet] Ignoring --name %r; using %r (no spaces allowed)",
            name,
            package_name,
        )

    extra_ignore = extra_ignore_dirs.split(",") if extra_ignore_dirs else None
    extra_mods: list[str] = []
    if extra_modules:
        for module in extra_modules.split(","):
            module = module.strip()
            if module.startswith("Qt"):
                extra_mods.append(module[2:])
            elif module:
                extra_mods.append(module)

    main_file = Path.cwd() / "main.py"
    if not main_file.exists():
        raise RuntimeError("main.py must exist in the project root")

    android_data = AndroidData(
        wheel_pyside=pyside_wheel,
        wheel_shiboken=shiboken_wheel,
        ndk_path=ndk_path,
        sdk_path=sdk_path,
    )
    python = PythonExecutable(dry_run=dry_run, init=init, force=force)
    config_exists = config_file.exists()
    config = AndroidConfig(
        config_file=config_file,
        source_file=main_file,
        python_exe=python.exe,
        dry_run=dry_run,
        android_data=android_data,
        existing_config_file=config_exists,
        extra_ignore_dirs=extra_ignore,
        name=package_name,
    )

    project_dir = Path(config.project_dir)
    purge_stale_android_cache(project_dir, force=clean_cache or force)

    cleanup(config=config, is_android=True)
    python.install_dependencies(config=config, packages="android_packages", is_android=True)

    try:
        config.modules += list(set(extra_mods).difference(set(config.modules)))
        config.jars_dir = config.find_jars_dir()
        config.recipe_dir = config.find_recipe_dir()

        Buildozer.dry_run = dry_run
        logging.info("[DEPLOY] Creating buildozer.spec file")
        write_buildozer_spec(config, project_dir)

        if not dry_run:
            config.update_config()

        if init:
            logging.info("[DEPLOY] Config file %s created", config.config_file)
            return 0

        logging.info("[DEPLOY] Running buildozer deployment")
        Buildozer.create_executable(config.mode)

        if not dry_run:
            buildozer_build_dir = project_dir / ".buildozer"
            if buildozer_build_dir.exists():
                shutil.move(buildozer_build_dir, config.generated_files_path)

        logging.info("[DEPLOY] apk created in %s", config.exe_dir)
        return 0
    except Exception:
        print(f"Exception occurred: {traceback.format_exc()}")
        return 1
    finally:
        if config.generated_files_path and config and not keep_deployment_files:
            cleanup(config=config, is_android=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy InfiniteRicks wallet to Android")
    parser.add_argument("-c", "--config-file", type=lambda p: Path(p).absolute(), required=True)
    parser.add_argument("--init", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_const", dest="loglevel", const=logging.INFO)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--keep-deployment-files", action="store_true", default=True)
    parser.add_argument("--clean-deployment-files", action="store_true")
    parser.add_argument("--clean-cache", action="store_true",
                        help="Remove .buildozer and buildozer.spec before building")
    parser.add_argument("-f", "--force", action="store_true")
    parser.add_argument("--name", type=str)
    parser.add_argument("--wheel-pyside", type=lambda p: Path(p).resolve(), required=True)
    parser.add_argument("--wheel-shiboken", type=lambda p: Path(p).resolve(), required=True)
    parser.add_argument("--ndk-path", type=lambda p: Path(p).resolve())
    parser.add_argument("--sdk-path", type=lambda p: Path(p).resolve())
    parser.add_argument("--extra-ignore-dirs", type=str)
    parser.add_argument("--extra-modules", type=str)
    args = parser.parse_args()

    if sys.version_info >= (3, 12):
        raise RuntimeError("Android deployment requires Python 3.11 or lower")

    return deploy(
        args.name,
        args.wheel_pyside,
        args.wheel_shiboken,
        args.ndk_path,
        args.sdk_path,
        args.config_file,
        args.init,
        args.loglevel or logging.WARNING,
        args.dry_run,
        args.force,
        args.extra_ignore_dirs,
        args.extra_modules,
        not args.clean_deployment_files,
        args.clean_cache,
    )


if __name__ == "__main__":
    raise SystemExit(main())
