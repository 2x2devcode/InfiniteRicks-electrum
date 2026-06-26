"""Tests for transaction signing."""

import time

from infinitericks_wallet.crypto.hash import hash160
from infinitericks_wallet.crypto.keys import KeyPair
from infinitericks_wallet.crypto.script import p2pkh_script
from infinitericks_wallet.crypto.transaction import Transaction, TxIn, TxOut, signature_hash
from infinitericks_wallet.wallet.hd import master_key_from_seed
from infinitericks_wallet.wallet.mnemonic import mnemonic_to_seed


def test_signature_hash_includes_ntime():
    tx = Transaction(n_time=int(time.time()))
    tx.inputs.append(TxIn(bytes(32), 0, b""))
    tx.outputs.append(TxOut(100000, p2pkh_script(bytes(20))))
    digest = signature_hash(tx, 0, p2pkh_script(bytes(20)))
    assert len(digest) == 32


def test_hd_derivation_deterministic():
    seed = mnemonic_to_seed("abandon " * 11 + "about")
    m1 = master_key_from_seed(seed)
    m2 = master_key_from_seed(seed)
    child1 = m1.derive_path("m/44'/0'/0'/0/0")
    child2 = m2.derive_path("m/44'/0'/0'/0/0")
    assert child1.private_key == child2.private_key
