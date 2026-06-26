#!/usr/bin/env python3
"""Android deploy wrapper: patch buildozer.spec with wallet requirements before build."""

from __future__ import annotations

import argparse
import logging
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


def patch_buildozer_spec(project_dir: Path) -> None:
    spec = project_dir / "buildozer.spec"
    if not spec.exists():
        return
    parser = ConfigParser(comment_prefixes="#", allow_no_value=True)
    parser.read(spec)
    if not parser.has_section("app"):
        return
    current = parser.get("app", "requirements", fallback="python3,shiboken6,PySide6")
    parts = [item.strip() for item in current.split(",") if item.strip()]
    for item in WALLET_REQUIREMENTS:
        if item not in parts:
            parts.append(item)
    parser.set("app", "requirements", ",".join(parts))
    if not parser.has_section("buildozer"):
        parser.add_section("buildozer")
    parser.set("buildozer", "warn_on_root", "0")
    if not parser.has_option("app", "android.accept_sdk_license"):
        parser.set("app", "android.accept_sdk_license", "True")
    with spec.open("w", encoding="utf-8") as handle:
        parser.write(handle)
    logging.info("[deploy_wallet] Updated buildozer.spec requirements")


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
    keep_deployment_files: bool = True,
    force: bool,
    extra_ignore_dirs: str | None,
    extra_modules: str | None,
) -> int:
    logging.basicConfig(level=loglevel)

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
        name=name,
    )

    cleanup(config=config, is_android=True)
    python.install_dependencies(config=config, packages="android_packages", is_android=True)

    try:
        config.modules += list(set(extra_mods).difference(set(config.modules)))
        config.jars_dir = config.find_jars_dir()
        config.recipe_dir = config.find_recipe_dir()

        Buildozer.dry_run = dry_run
        logging.info("[DEPLOY] Creating buildozer.spec file")
        Buildozer.initialize(pysidedeploy_config=config)
        patch_buildozer_spec(Path(config.project_dir))

        if not dry_run:
            config.update_config()

        if init:
            logging.info("[DEPLOY] Config file %s created", config.config_file)
            return 0

        logging.info("[DEPLOY] Running buildozer deployment")
        Buildozer.create_executable(config.mode)

        if not dry_run:
            buildozer_build_dir = config.project_dir / ".buildozer"
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
        not args.clean_deployment_files,
        args.force,
        args.extra_ignore_dirs,
        args.extra_modules,
    )


if __name__ == "__main__":
    raise SystemExit(main())
