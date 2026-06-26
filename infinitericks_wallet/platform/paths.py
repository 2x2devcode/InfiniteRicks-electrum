"""Writable application data paths (desktop and Android)."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _android_files_dir() -> Path | None:
    private = os.environ.get("ANDROID_PRIVATE")
    if private:
        return Path(private)
    argument = os.environ.get("ANDROID_ARGUMENT")
    if argument:
        return Path(argument)
    return None


def app_data_dir() -> Path:
    """Return the directory for wallet files and SPV headers."""
    android_dir = _android_files_dir()
    if android_dir is not None:
        return android_dir / "infinitericks_wallet"

    try:
        from PySide6.QtCore import QCoreApplication, QStandardPaths

        if QCoreApplication.instance() is not None:
            location = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            if location:
                return Path(location)
    except Exception:
        pass

    return Path.home() / ".infinitericks_wallet"


def wallet_file() -> Path:
    return app_data_dir() / "wallet.enc"


def headers_file() -> Path:
    return app_data_dir() / "headers.json"


def is_android_runtime() -> bool:
    return sys.platform == "android" or _android_files_dir() is not None
