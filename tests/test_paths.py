"""Tests for platform paths."""

from pathlib import Path

from infinitericks_wallet.platform import paths


def test_app_data_dir_fallback(monkeypatch):
    monkeypatch.delenv("ANDROID_PRIVATE", raising=False)
    monkeypatch.delenv("ANDROID_ARGUMENT", raising=False)
    monkeypatch.setattr(paths, "Path", Path)
    data_dir = paths.app_data_dir()
    assert data_dir.name == ".infinitericks_wallet" or data_dir.parts[-1] == "infinitericks_wallet"


def test_android_private_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("ANDROID_PRIVATE", str(tmp_path))
    assert paths.app_data_dir() == tmp_path / "infinitericks_wallet"
    assert paths.wallet_file() == tmp_path / "infinitericks_wallet" / "wallet.enc"
