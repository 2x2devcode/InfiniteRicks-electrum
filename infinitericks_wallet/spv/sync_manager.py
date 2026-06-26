"""SPV synchronization manager."""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Optional

from infinitericks_wallet.config.chainparams import ACTIVE_NETWORK, COIN
from infinitericks_wallet.crypto.block import BlockHeader, parse_electrum_header
from infinitericks_wallet.crypto.merkle import verify_merkle_proof
from infinitericks_wallet.crypto.transaction import Transaction
from infinitericks_wallet.network.electrum_client import ElectrumClient, ElectrumClientError
from infinitericks_wallet.spv.header_store import HeaderStore
from infinitericks_wallet.wallet.utxo import UTXO
from infinitericks_wallet.wallet.wallet import TxHistoryItem, Wallet

logger = logging.getLogger(__name__)


class SyncManager:
    def __init__(
        self,
        wallet: Wallet,
        on_update: Optional[Callable[[], None]] = None,
    ) -> None:
        self.wallet = wallet
        self.client = ElectrumClient(on_notification=self._on_notification)
        self.headers = HeaderStore()
        self._on_update = on_update
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._tip_height = 0
        self._lock = threading.Lock()

    @property
    def connected(self) -> bool:
        return self.client.connected

    @property
    def tip_height(self) -> int:
        return self._tip_height

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        self.client.disconnect()

    def _sync_loop(self) -> None:
        while self._running:
            try:
                if not self.client.connected:
                    self.client.connect()
                self._sync_headers()
                self._sync_addresses()
                self._notify()
            except ElectrumClientError as exc:
                logger.error("Sync error: %s", exc)
                time.sleep(5)
            except Exception as exc:
                logger.exception("Unexpected sync error: %s", exc)
                time.sleep(10)
            time.sleep(30)

    def sync_now(self) -> None:
        if not self.client.connected:
            self.client.connect()
        self._sync_headers()
        self._sync_addresses()
        self._notify()

    def _sync_headers(self) -> None:
        header_hex, height = self.client.subscribe_headers()
        header = parse_electrum_header(header_hex, height)
        block_hash = header.hash_hex()

        if height > self.headers.tip_height:
            start = self.headers.tip_height + 1
            if start == 0:
                genesis = ACTIVE_NETWORK.genesis_hash
                self.headers.add_header(0, header_hex, genesis if start == height else block_hash)
                start = 1
            batch_size = min(2016, height - start + 1)
            if batch_size > 0 and start <= height:
                result = self.client.get_headers(start, batch_size)
                raw = result.get("hex", "")
                count = result.get("count", 0)
                for i in range(count):
                    offset = i * 160  # ElectrumX returns hex header * 2 + count
                    h_hex = raw[i * 160:(i + 1) * 160] if len(raw) >= (i + 1) * 160 else raw[i * 160:]
                    if len(h_hex) >= 160:
                        h_data = bytes.fromhex(h_hex[:160])
                        h = BlockHeader.deserialize(h_data, start + i)
                        self.headers.add_header(start + i, h_hex[:160], h.hash_hex())

        self.headers.add_header(height, header_hex, block_hash)
        self.headers.save()
        self._tip_height = height
        self.wallet.utxos.update_confirmations(height)

    def _sync_addresses(self) -> None:
        from infinitericks_wallet.crypto.address import Address

        for addr_info in self.wallet.addresses:
            sh = Address.from_string(addr_info.address).scripthash
            try:
                self.client.subscribe_scripthash(sh)
                history = self.client.get_history(sh)
                for item in history:
                    self._process_history_item(item, addr_info.address)
            except ElectrumClientError as exc:
                logger.warning("Address sync failed for %s: %s", addr_info.address, exc)

    def _process_history_item(self, item: dict, address: str) -> None:
        tx_hash = item.get("tx_hash", "")
        height = item.get("height", 0)
        if not tx_hash:
            return

        try:
            raw_hex = self.client.get_transaction(tx_hash)
            tx = Transaction.deserialize(bytes.fromhex(raw_hex))
            value = 0
            for out in tx.outputs:
                from infinitericks_wallet.crypto.address import Address

                for a in self.wallet.addresses:
                    addr_obj = Address.from_string(a.address)
                    if out.script_pubkey == addr_obj.script:
                        value += out.value
                        self.wallet.utxos.add(
                            UTXO(tx_hash, tx.outputs.index(out), out.value, out.script_pubkey, a.address, height)
                        )

            confirmations = max(0, self._tip_height - height + 1) if height > 0 else 0
            self.wallet.add_history_item(
                TxHistoryItem(tx_hash, height, value, tx.n_time, confirmations, addresses=[address])
            )

            if height > 0:
                merkle = self.client.get_merkle(tx_hash, height)
                header_entry = self.headers.get_header(height)
                if header_entry and merkle:
                    verify_merkle_proof(
                        tx_hash,
                        header_entry.get("merkle", ""),
                        height,
                        merkle.get("merkle", []),
                        merkle.get("pos", 0),
                    )
        except Exception as exc:
            logger.warning("Failed to process tx %s: %s", tx_hash, exc)

    def _on_notification(self, method: str, params: list) -> None:
        if method in ("blockchain.headers.subscribe", "blockchain.scripthash.subscribe"):
            threading.Thread(target=self.sync_now, daemon=True).start()

    def _notify(self) -> None:
        if self._on_update:
            self._on_update()

    def broadcast_transaction(self, raw_hex: str) -> str:
        return self.client.broadcast(raw_hex)
