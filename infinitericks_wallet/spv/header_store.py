"""Local block header storage."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from infinitericks_wallet.crypto.block import BlockHeader
from infinitericks_wallet.platform.paths import headers_file


class HeaderStore:
    def __init__(self, path: Optional[Path] = None) -> None:
        self._path = path or headers_file()
        self._headers: Dict[int, dict] = {}
        self._tip_height: int = 0
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            data = json.loads(self._path.read_text())
            self._headers = {int(k): v for k, v in data.get("headers", {}).items()}
            self._tip_height = data.get("tip", 0)

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps({"tip": self._tip_height, "headers": self._headers}, indent=2))

    def add_header(self, height: int, header_hex: str, header_hash: str) -> None:
        header = BlockHeader.deserialize(bytes.fromhex(header_hex), height)
        self._headers[height] = {
            "hex": header_hex,
            "hash": header_hash,
            "prev": header.prev_block[::-1].hex(),
            "timestamp": header.timestamp,
        }
        if height > self._tip_height:
            self._tip_height = height

    def get_header(self, height: int) -> Optional[dict]:
        return self._headers.get(height)

    @property
    def tip_height(self) -> int:
        return self._tip_height

    def verify_chain(self, from_height: int = 1) -> bool:
        from infinitericks_wallet.crypto.block import BlockHeader

        for h in range(from_height, self._tip_height + 1):
            if h not in self._headers:
                return False
            entry = self._headers[h]
            header = BlockHeader.deserialize(bytes.fromhex(entry["hex"]), h)
            if header.hash_hex() != entry["hash"]:
                return False
            if h > 0 and h - 1 in self._headers:
                prev_hash = self._headers[h - 1]["hash"]
                if header.prev_block[::-1].hex() != prev_hash:
                    return False
        return True

    def handle_reorg(self, new_tip_height: int, new_headers: List[tuple]) -> int:
        """Apply reorg: remove headers above fork point, add new chain."""
        fork_height = new_tip_height - len(new_headers)
        for h in list(self._headers.keys()):
            if h > fork_height:
                del self._headers[h]
        for i, (hex_hdr, hash_hdr) in enumerate(new_headers):
            self.add_header(fork_height + 1 + i, hex_hdr, hash_hdr)
        self.save()
        return fork_height
