"""Transaction signing and building."""

from __future__ import annotations

import time
from typing import List, Tuple

from infinitericks_wallet.config.chainparams import MIN_TX_FEE, TX_VERSION
from infinitericks_wallet.crypto.address import Address
from infinitericks_wallet.crypto.hash import hash160
from infinitericks_wallet.crypto.keys import KeyPair
from infinitericks_wallet.crypto.script import make_p2pkh_scriptsig, p2pkh_script
from infinitericks_wallet.crypto.transaction import Transaction, TxIn, TxOut, signature_hash
from infinitericks_wallet.wallet.utxo import UTXO


def estimate_fee(num_inputs: int, num_outputs: int, fee_rate: int) -> int:
    size = 10 + 148 * num_inputs + 34 * num_outputs + 4  # nTime adds 4 bytes
    fee = size * fee_rate
    return max(fee, MIN_TX_FEE)


def build_transaction(
    utxos: List[UTXO],
    recipient: str,
    amount: int,
    change_address: str,
    fee: int,
    keypairs: dict,
) -> Transaction:
    total_in = sum(u.value for u in utxos)
    if total_in < amount + fee:
        raise ValueError("Insufficient funds including fee")

    tx = Transaction(version=TX_VERSION, n_time=int(time.time()))
    for utxo in utxos:
        tx.inputs.append(
            TxIn(bytes.fromhex(utxo.tx_hash)[::-1], utxo.tx_pos, b"")
        )

    recipient_addr = Address.from_string(recipient)
    tx.outputs.append(TxOut(amount, recipient_addr.script))

    change = total_in - amount - fee
    if change > 0:
        change_addr = Address.from_string(change_address)
        tx.outputs.append(TxOut(change, change_addr.script))

    for i, utxo in enumerate(utxos):
        kp: KeyPair = keypairs[utxo.address]
        script_code = p2pkh_script(hash160(kp.public_key))
        digest = signature_hash(tx, i, script_code)
        sig = kp.sign_der(digest)
        tx.inputs[i].script_sig = make_p2pkh_scriptsig(sig, kp.public_key)

    return tx
