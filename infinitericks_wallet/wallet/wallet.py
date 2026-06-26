"""Core wallet logic."""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from infinitericks_wallet.config.chainparams import ACTIVE_NETWORK, COIN
from infinitericks_wallet.crypto.address import Address, pubkey_to_address, validate_address
from infinitericks_wallet.crypto.keys import KeyPair
from infinitericks_wallet.crypto.transaction import Transaction
from infinitericks_wallet.wallet.hd import HDKey, derive_address_key, master_key_from_seed
from infinitericks_wallet.wallet.mnemonic import generate_mnemonic, mnemonic_to_seed, validate_mnemonic
from infinitericks_wallet.wallet.signing import build_transaction, estimate_fee
from infinitericks_wallet.wallet.utxo import UTXO, UTXOManager


@dataclass
class AddressInfo:
    address: str
    label: str
    derivation_path: str
    index: int
    used: bool = False


@dataclass
class TxHistoryItem:
    tx_hash: str
    height: int
    value: int
    timestamp: int
    confirmations: int
    fee: int = 0
    addresses: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "tx_hash": self.tx_hash,
            "height": self.height,
            "value": self.value,
            "timestamp": self.timestamp,
            "confirmations": self.confirmations,
            "fee": self.fee,
            "addresses": self.addresses,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TxHistoryItem":
        return cls(**data)


class Wallet:
    def __init__(self) -> None:
        self.mnemonic: str = ""
        self.master_key: Optional[HDKey] = None
        self.addresses: List[AddressInfo] = []
        self.utxos = UTXOManager()
        self.history: List[TxHistoryItem] = []
        self.address_book: Dict[str, str] = {}
        self._keypairs: Dict[str, KeyPair] = {}
        self._next_index: int = 0

    @classmethod
    def create_new(cls) -> tuple["Wallet", str]:
        wallet = cls()
        mnemonic = generate_mnemonic(128)
        wallet.load_from_mnemonic(mnemonic)
        return wallet, mnemonic

    def load_from_mnemonic(self, mnemonic: str) -> None:
        if not validate_mnemonic(mnemonic):
            raise ValueError("Invalid mnemonic phrase")
        self.mnemonic = mnemonic
        seed = mnemonic_to_seed(mnemonic)
        self.master_key = master_key_from_seed(seed)
        self.addresses.clear()
        self._keypairs.clear()
        self._next_index = 0
        self.generate_address("Primary")

    def generate_address(self, label: str = "") -> AddressInfo:
        if not self.master_key:
            raise RuntimeError("Wallet not initialized")
        child, path = derive_address_key(self.master_key, 0, self._next_index)
        kp = child.keypair()
        addr = pubkey_to_address(kp.public_key)
        self._keypairs[addr] = kp
        info = AddressInfo(addr, label or f"Address {self._next_index + 1}", path, self._next_index)
        self.addresses.append(info)
        self._next_index += 1
        return info

    def get_receive_address(self) -> AddressInfo:
        unused = [a for a in self.addresses if not a.used]
        if unused:
            return unused[0]
        return self.generate_address()

    def balance(self) -> int:
        return self.utxos.balance()

    def balance_rick(self) -> float:
        return self.balance() / COIN

    def get_keypair(self, address: str) -> KeyPair:
        if address not in self._keypairs:
            raise KeyError(f"No key for address {address}")
        return self._keypairs[address]

    def scripthashes(self) -> List[str]:
        return [Address.from_string(a.address).scripthash for a in self.addresses]

    def address_for_scripthash(self, scripthash: str) -> Optional[str]:
        for a in self.addresses:
            if Address.from_string(a.address).scripthash == scripthash:
                return a.address
        return None

    def create_send_tx(self, recipient: str, amount: int, fee_rate: int, change_addr: Optional[str] = None) -> Transaction:
        if not validate_address(recipient):
            raise ValueError("Invalid recipient address")
        change = change_addr or self.addresses[0].address
        utxos = self.utxos.select_coins(amount, estimate_fee(1, 2, fee_rate))
        fee = estimate_fee(len(utxos), 2, fee_rate)
        return build_transaction(utxos, recipient, amount, change, fee, self._keypairs)

    def add_history_item(self, item: TxHistoryItem) -> None:
        existing = {h.tx_hash for h in self.history}
        if item.tx_hash not in existing:
            self.history.insert(0, item)
        else:
            for i, h in enumerate(self.history):
                if h.tx_hash == item.tx_hash:
                    self.history[i] = item
                    break

    def recent_history(self, limit: int = 5) -> List[TxHistoryItem]:
        return sorted(self.history, key=lambda h: h.height, reverse=True)[:limit]

    def to_dict(self) -> dict:
        return {
            "mnemonic": self.mnemonic,
            "addresses": [
                {"address": a.address, "label": a.label, "path": a.derivation_path, "index": a.index, "used": a.used}
                for a in self.addresses
            ],
            "utxos": self.utxos.to_list(),
            "history": [h.to_dict() for h in self.history],
            "address_book": self.address_book,
            "next_index": self._next_index,
        }

    def load_dict(self, data: dict) -> None:
        self.mnemonic = data.get("mnemonic", "")
        if self.mnemonic:
            seed = mnemonic_to_seed(self.mnemonic)
            self.master_key = master_key_from_seed(seed)
        self.addresses = [
            AddressInfo(a["address"], a["label"], a["path"], a["index"], a.get("used", False))
            for a in data.get("addresses", [])
        ]
        self._next_index = data.get("next_index", len(self.addresses))
        self._keypairs.clear()
        for a in self.addresses:
            if self.master_key:
                child = self.master_key.derive_path(a.derivation_path)
                self._keypairs[a.address] = child.keypair()
        self.utxos.load_list(data.get("utxos", []))
        self.history = [TxHistoryItem.from_dict(h) for h in data.get("history", [])]
        self.address_book = data.get("address_book", {})
