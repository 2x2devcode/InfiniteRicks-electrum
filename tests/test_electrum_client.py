"""Tests for Electrum client platform timeouts."""

from infinitericks_wallet.network import electrum_client


def test_android_shorter_timeouts(monkeypatch):
    monkeypatch.setenv("ANDROID_PRIVATE", "/data/data/com.example/files")
    connect, request, attempts, delay = electrum_client._client_timeouts()
    assert connect == 8
    assert request == 30
    assert attempts == 3
    assert delay == 1.5


def test_desktop_timeouts(monkeypatch):
    monkeypatch.delenv("ANDROID_PRIVATE", raising=False)
    monkeypatch.delenv("ANDROID_ARGUMENT", raising=False)
    connect, request, attempts, delay = electrum_client._client_timeouts()
    assert connect == 30
    assert request == 60
    assert attempts == 10
