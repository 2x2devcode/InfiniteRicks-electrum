#!/usr/bin/env python3
"""Test connectivity to configured ElectrumX SPV servers."""

from __future__ import annotations

import json
import socket
import ssl
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from infinitericks_wallet.config.chainparams import ELECTRUM_SERVERS  # noqa: E402


def probe(host: str, port: int, use_ssl: bool, timeout: float = 10.0) -> tuple[bool, str]:
    try:
        raw = socket.create_connection((host, port), timeout=timeout)
        if use_ssl:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            sock = ctx.wrap_socket(raw, server_hostname=host)
        else:
            sock = raw
        sock.settimeout(timeout)
        payload = json.dumps(
            {"jsonrpc": "2.0", "method": "server.version", "params": ["1.4", "1.0"], "id": 1}
        )
        sock.sendall((payload + "\n").encode())
        buf = b""
        while b"\n" not in buf:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk
        sock.close()
        if not buf.strip():
            return False, "porta aberta, mas sem resposta Electrum"
        data = json.loads(buf.decode().split("\n", 1)[0])
        if "result" in data:
            return True, f"OK — server.version = {data['result']}"
        return False, f"resposta inesperada: {buf.decode(errors='replace')[:120]}"
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    print("Testando servidores SPV (ElectrumX)...\n")
    any_ok = False
    for host, port, use_ssl in ELECTRUM_SERVERS:
        label = f"{host}:{port} ({'TLS' if use_ssl else 'TCP'})"
        ok, detail = probe(host, port, use_ssl)
        status = "OK" if ok else "FALHOU"
        print(f"[{status}] {label}")
        print(f"        {detail}\n")
        any_ok = any_ok or ok

    if any_ok:
        print("Pelo menos um servidor respondeu. Se a carteira ainda mostra No Connection,")
        print("verifique firewall local ou tente reiniciar o app.")
        return 0

    print("Nenhum servidor SPV respondeu.")
    print("A carteira funciona offline (criar/importar endereços), mas saldo e transações")
    print("só sincronizam quando o ElectrumX estiver online.")
    print("\nPeça ao operador da rede para restaurar o ElectrumX ou configure outro servidor")
    print("em infinitericks_wallet/config/chainparams.py (ELECTRUM_SERVERS).")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
