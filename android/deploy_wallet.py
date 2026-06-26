#!/usr/bin/env python3
"""Android deploy wrapper: write buildozer.spec and purge p4a cache before build."""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
import sys
import traceback
from configparser import ConfigParser
from pathlib import Path

import PySide6

sys.path.insert(0, str(Path(PySide6.__file__).resolve().parent / "scripts"))

from deploy_lib import cleanup, PythonExecutable
from deploy_lib.android import AndroidData, AndroidConfig
from deploy_lib.android.buildozer import Buildozer, BuildozerConfig

DEPLOY_WALLET_VERSION = 5

BUNDLED_RECIPES_DIR = Path(__file__).resolve().parent / "recipes"

# Built before argon2-cffi/cryptography (cffi needs pycparser at host setup time).
P4A_BUILD_DEPS = (
    "setuptools",
    "pycparser",
    "cffi",
)

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
HOSTPYTHON_REQUIREMENT = f"hostpython3=={ANDROID_PYTHON_VERSION}"


def _read_buildozer_spec(project_dir: Path) -> ConfigParser | None:
    spec = project_dir / "buildozer.spec"
    if not spec.exists():
        return None
    parser = ConfigParser(comment_prefixes="#", allow_no_value=True)
    parser.read(spec)
    return parser


def purge_android_cache(project_dir: Path) -> None:
    """Always remove buildozer state before generating a new spec."""
    removed: list[str] = []
    for rel in (".buildozer", "buildozer.spec"):
        target = project_dir / rel
        if not target.exists():
            continue
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        removed.append(rel)
    if removed:
        logging.warning("[deploy_wallet] Cleared Android cache: %s", ", ".join(removed))


def install_custom_recipes(recipe_dir: Path | None) -> None:
    """Copy bundled p4a recipe overrides into the generated recipes directory."""
    if recipe_dir is None or not BUNDLED_RECIPES_DIR.is_dir():
        return
    recipe_dir.mkdir(parents=True, exist_ok=True)
    for bundled in BUNDLED_RECIPES_DIR.iterdir():
        if not bundled.is_dir():
            continue
        dest = recipe_dir / bundled.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(bundled, dest)
        logging.info("[deploy_wallet] Installed p4a recipe override: %s", bundled.name)


def patch_buildozer_spec(project_dir: Path, config: AndroidConfig) -> None:
    spec = project_dir / "buildozer.spec"
    if not spec.exists():
        raise RuntimeError(f"buildozer.spec missing in {project_dir}")

    parser = ConfigParser(comment_prefixes="#", allow_no_value=True)
    parser.read(spec)
    if not parser.has_section("app"):
        raise RuntimeError("buildozer.spec has no [app] section")

    requirements = [
        HOSTPYTHON_REQUIREMENT,
        PYTHON_REQUIREMENT,
        "shiboken6",
        "PySide6",
        *P4A_BUILD_DEPS,
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


def verify_buildozer_spec(project_dir: Path) -> None:
    spec = project_dir / "buildozer.spec"
    text = spec.read_text(encoding="utf-8")
    if "InfiniteRicks Wallet" in text:
        raise RuntimeError(
            "buildozer.spec still contains 'InfiniteRicks Wallet'. "
            "Spaces in dist_name break NDK cross-compile."
        )

    parser = _read_buildozer_spec(project_dir)
    if parser is None:
        raise RuntimeError("buildozer.spec was not created")

    package_name = parser.get("app", "package.name", fallback="")
    requirements = parser.get("app", "requirements", fallback="")
    if package_name != ANDROID_PACKAGE_NAME or " " in package_name:
        raise RuntimeError(
            f"Invalid package.name '{package_name}' — must be '{ANDROID_PACKAGE_NAME}'"
        )
    if PYTHON_REQUIREMENT not in requirements.replace(" ", ""):
        raise RuntimeError(
            f"buildozer.spec must pin {PYTHON_REQUIREMENT}, got: {requirements}"
        )
    if HOSTPYTHON_REQUIREMENT not in requirements.replace(" ", ""):
        raise RuntimeError(
            f"buildozer.spec must pin {HOSTPYTHON_REQUIREMENT}, got: {requirements}"
        )

    logging.info(
        "[deploy_wallet] Verified buildozer.spec: package.name=%s requirements=%s",
        package_name,
        requirements,
    )


def write_buildozer_spec(config: AndroidConfig, project_dir: Path) -> None:
    """Regenerate buildozer.spec from scratch on every deploy."""
    purge_android_cache(project_dir)

    Buildozer.dry_run = config.dry_run
    command = [sys.executable, "-m", "buildozer", "init"]
    if not config.dry_run:
        subprocess.check_call(command, cwd=project_dir)

    spec = project_dir / "buildozer.spec"
    if not config.dry_run and not spec.exists():
        raise RuntimeError(f"buildozer init did not create {spec}")

    if not config.dry_run:
        BuildozerConfig(spec, config)
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
    keep_cache: bool = False,
) -> int:
    logging.basicConfig(level=loglevel)
    logging.info("[deploy_wallet] version %s", DEPLOY_WALLET_VERSION)

    if name and name != ANDROID_PACKAGE_NAME:
        logging.warning(
            "[deploy_wallet] Ignoring --name %r; using %r",
            name,
            ANDROID_PACKAGE_NAME,
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
        name=ANDROID_PACKAGE_NAME,
    )

    project_dir = Path(config.project_dir)
    if keep_cache:
        logging.info("[deploy_wallet] Keeping existing .buildozer cache (--keep-cache)")
    else:
        purge_android_cache(project_dir)

    cleanup(config=config, is_android=True)
    python.install_dependencies(config=config, packages="android_packages", is_android=True)

    try:
        config.modules += list(set(extra_mods).difference(set(config.modules)))
        config.jars_dir = config.find_jars_dir()
        config.recipe_dir = config.find_recipe_dir()
        install_custom_recipes(config.recipe_dir)

        logging.info("[DEPLOY] Creating buildozer.spec file")
        if keep_cache:
            spec = project_dir / "buildozer.spec"
            if spec.exists():
                spec.unlink()
            Buildozer.initialize(pysidedeploy_config=config)
            patch_buildozer_spec(project_dir, config)
        else:
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
    parser.add_argument(
        "--keep-cache",
        action="store_true",
        help="Reuse .buildozer cache (not recommended; breaks after config changes)",
    )
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
        args.keep_cache,
    )


if __name__ == "__main__":
    raise SystemExit(main())
