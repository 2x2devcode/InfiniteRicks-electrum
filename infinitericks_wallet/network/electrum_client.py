"""ElectrumX JSON-RPC protocol client over TLS."""

from __future__ import annotations

import json
import logging
import socket
import ssl
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from infinitericks_wallet.config.chainparams import (
    CONNECT_TIMEOUT,
    ELECTRUM_PROTOCOL_VERSION,
    ELECTRUM_SERVERS,
    MAX_RECONNECT_ATTEMPTS,
    RECONNECT_DELAY_BASE,
    REQUEST_TIMEOUT,
)

logger = logging.getLogger(__name__)


class ElectrumClientError(Exception):
    pass


class ElectrumClient:
    def __init__(
        self,
        servers: Optional[List[Tuple[str, int, bool]]] = None,
        on_notification: Optional[Callable[[str, Any], None]] = None,
    ) -> None:
        self._servers = servers or list(ELECTRUM_SERVERS)
        self._server_index = 0
        self._sock: Optional[ssl.SSLSocket] = None
        self._request_id = 0
        self._lock = threading.Lock()
        self._buffer = b""
        self._connected = False
        self._on_notification = on_notification
        self._reader_thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def current_server(self) -> str:
        host, port, _ = self._servers[self._server_index]
        return f"{host}:{port}"

    def connect(self) -> None:
        last_error: Optional[Exception] = None
        for attempt in range(MAX_RECONNECT_ATTEMPTS):
            host, port, use_ssl = self._servers[self._server_index]
            try:
                raw_sock = socket.create_connection((host, port), timeout=CONNECT_TIMEOUT)
                if use_ssl:
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    self._sock = ctx.wrap_socket(raw_sock, server_hostname=host)
                else:
                    self._sock = raw_sock  # type: ignore
                self._sock.settimeout(REQUEST_TIMEOUT)
                self._connected = True
                self._stop.clear()
                self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
                self._reader_thread.start()
                self.request("server.version", [ELECTRUM_PROTOCOL_VERSION[0], "1.0"])
                logger.info("Connected to ElectrumX server %s:%d", host, port)
                return
            except Exception as exc:
                last_error = exc
                logger.warning("Connection attempt %d failed: %s", attempt + 1, exc)
                self._disconnect()
                self._server_index = (self._server_index + 1) % len(self._servers)
                time.sleep(RECONNECT_DELAY_BASE ** min(attempt, 5))
        raise ElectrumClientError(f"Failed to connect: {last_error}")

    def _disconnect(self) -> None:
        self._connected = False
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None

    def disconnect(self) -> None:
        self._stop.set()
        self._disconnect()

    def _read_loop(self) -> None:
        while not self._stop.is_set() and self._connected and self._sock:
            try:
                data = self._sock.recv(65536)
                if not data:
                    break
                self._buffer += data
                self._process_buffer()
            except socket.timeout:
                continue
            except Exception as exc:
                logger.error("Read error: %s", exc)
                break
        self._connected = False

    def _process_buffer(self) -> None:
        while True:
            try:
                idx = self._buffer.index(b"\n")
            except ValueError:
                break
            line = self._buffer[:idx]
            self._buffer = self._buffer[idx + 1:]
            if not line.strip():
                continue
            try:
                msg = json.loads(line.decode("utf-8"))
            except json.JSONDecodeError:
                continue
            if "method" in msg and "id" not in msg:
                if self._on_notification:
                    self._on_notification(msg["method"], msg.get("params", []))

    def request(self, method: str, params: Optional[List[Any]] = None) -> Any:
        if not self._connected or not self._sock:
            raise ElectrumClientError("Not connected")
        with self._lock:
            self._request_id += 1
            req_id = self._request_id
            payload = json.dumps({"jsonrpc": "2.0", "method": method, "params": params or [], "id": req_id})
            try:
                self._sock.sendall((payload + "\n").encode("utf-8"))
                deadline = time.time() + REQUEST_TIMEOUT
                while time.time() < deadline:
                    for line in self._buffer.split(b"\n"):
                        if not line.strip():
                            continue
                        try:
                            resp = json.loads(line.decode("utf-8"))
                        except json.JSONDecodeError:
                            continue
                        if resp.get("id") == req_id:
                            self._buffer = b""
                            if "error" in resp and resp["error"]:
                                raise ElectrumClientError(resp["error"].get("message", str(resp["error"])))
                            return resp.get("result")
                    try:
                        chunk = self._sock.recv(65536)
                        if chunk:
                            self._buffer += chunk
                        else:
                            break
                    except socket.timeout:
                        continue
                raise ElectrumClientError(f"Request timeout: {method}")
            except ElectrumClientError:
                raise
            except Exception as exc:
                self._connected = False
                raise ElectrumClientError(str(exc)) from exc

    def subscribe_headers(self) -> Tuple[str, int]:
        result = self.request("blockchain.headers.subscribe")
        if isinstance(result, list) and len(result) >= 2:
            return result[0], result[1]
        raise ElectrumClientError("Invalid headers.subscribe response")

    def get_header(self, height: int) -> str:
        return self.request("blockchain.block.header", [height])

    def subscribe_scripthash(self, scripthash: str) -> str:
        return self.request("blockchain.scripthash.subscribe", [scripthash])

    def get_history(self, scripthash: str) -> List[dict]:
        return self.request("blockchain.scripthash.get_history", [scripthash]) or []

    def get_balance(self, scripthash: str) -> dict:
        return self.request("blockchain.scripthash.get_balance", [scripthash]) or {"confirmed": 0, "unconfirmed": 0}

    def get_transaction(self, tx_hash: str) -> str:
        return self.request("blockchain.transaction.get", [tx_hash])

    def get_merkle(self, tx_hash: str, height: int) -> dict:
        return self.request("blockchain.transaction.get_merkle", [tx_hash, height])

    def broadcast(self, raw_tx_hex: str) -> str:
        return self.request("blockchain.transaction.broadcast", [raw_tx_hex])

    def get_headers(self, start_height: int, count: int) -> dict:
        return self.request("blockchain.block.headers", [start_height, count])
