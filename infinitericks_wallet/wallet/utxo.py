"""UTXO management."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class UTXO:
    tx_hash: str
    tx_pos: int
    value: int
    script_pubkey: bytes
    address: str
    height: int = 0
    confirmations: int = 0

    @property
    def outpoint(self) -> Tuple[str, int]:
        return self.tx_hash, self.tx_pos

    def to_dict(self) -> dict:
        return {
            "tx_hash": self.tx_hash,
            "tx_pos": self.tx_pos,
            "value": self.value,
            "script_pubkey": self.script_pubkey.hex(),
            "address": self.address,
            "height": self.height,
            "confirmations": self.confirmations,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UTXO":
        return cls(
            data["tx_hash"],
            data["tx_pos"],
            data["value"],
            bytes.fromhex(data["script_pubkey"]),
            data["address"],
            data.get("height", 0),
            data.get("confirmations", 0),
        )


class UTXOManager:
    def __init__(self) -> None:
        self._utxos: Dict[Tuple[str, int], UTXO] = {}
        self._spent: Set[Tuple[str, int]] = set()

    def add(self, utxo: UTXO) -> None:
        self._utxos[utxo.outpoint] = utxo

    def mark_spent(self, tx_hash: str, tx_pos: int) -> None:
        key = (tx_hash, tx_pos)
        self._spent.add(key)
        self._utxos.pop(key, None)

    def get_spendable(self, min_confirmations: int = 1) -> List[UTXO]:
        return [
            u for u in self._utxos.values()
            if u.outpoint not in self._spent and u.confirmations >= min_confirmations
        ]

    def balance(self, min_confirmations: int = 1) -> int:
        return sum(u.value for u in self.get_spendable(min_confirmations))

    def select_coins(self, amount: int, fee: int, min_confirmations: int = 1) -> List[UTXO]:
        target = amount + fee
        coins = sorted(self.get_spendable(min_confirmations), key=lambda u: u.value)
        selected: List[UTXO] = []
        total = 0
        for coin in coins:
            selected.append(coin)
            total += coin.value
            if total >= target:
                return selected
        raise ValueError("Insufficient funds")

    def update_confirmations(self, tip_height: int) -> None:
        for utxo in self._utxos.values():
            if utxo.height > 0:
                utxo.confirmations = max(0, tip_height - utxo.height + 1)

    def to_list(self) -> List[dict]:
        return [u.to_dict() for u in self._utxos.values()]

    def load_list(self, items: List[dict]) -> None:
        self._utxos.clear()
        for item in items:
            utxo = UTXO.from_dict(item)
            self._utxos[utxo.outpoint] = utxo
