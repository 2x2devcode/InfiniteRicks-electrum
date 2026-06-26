"""Send coins screen."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from infinitericks_wallet.config.chainparams import COIN, FEE_RATE_FAST, FEE_RATE_NORMAL
from infinitericks_wallet.crypto.address import validate_address
from infinitericks_wallet.wallet.signing import estimate_fee


class SendScreen(QWidget):
    send_requested = Signal(str, int, int)
    back_clicked = Signal()
    save_address = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Enviar RICK"))
        layout.addWidget(QLabel("Endereço:"))
        addr_row = QHBoxLayout()
        self._address = QLineEdit()
        self._address.setPlaceholderText("Endereço InfiniteRicks")
        addr_row.addWidget(self._address)
        layout.addLayout(addr_row)

        layout.addWidget(QLabel("Valor (RICK):"))
        self._amount = QDoubleSpinBox()
        self._amount.setDecimals(8)
        self._amount.setMaximum(21_000_000_000)
        layout.addWidget(self._amount)

        layout.addWidget(QLabel("Taxa:"))
        self._fee_tier = QComboBox()
        self._fee_tier.addItems(["Normal", "Fast"])
        self._fee_tier.currentIndexChanged.connect(self._update_totals)
        layout.addWidget(self._fee_tier)

        self._summary = QLabel()
        layout.addWidget(self._summary)

        self._amount.valueChanged.connect(self._update_totals)
        self._error = QLabel("")
        self._error.setStyleSheet("color: #f85149;")
        layout.addWidget(self._error)

        self._btn_send = QPushButton("Enviar")
        self._btn_send.clicked.connect(self._confirm_send)
        layout.addWidget(self._btn_send)

        btn_back = QPushButton("Voltar")
        btn_back.setStyleSheet("background-color: #21262d;")
        btn_back.clicked.connect(self.back_clicked.emit)
        layout.addWidget(btn_back)

        self._update_totals()

    def _fee_rate(self) -> int:
        return FEE_RATE_FAST if self._fee_tier.currentIndex() == 1 else FEE_RATE_NORMAL

    def _update_totals(self) -> None:
        amount_sat = int(self._amount.value() * COIN)
        fee = estimate_fee(1, 2, self._fee_rate())
        total = amount_sat + fee
        self._summary.setText(
            f"Valor: {amount_sat / COIN:.8f} RICK\n"
            f"Taxa: {fee / COIN:.8f} RICK\n"
            f"Total: {total / COIN:.8f} RICK"
        )

    def _confirm_send(self) -> None:
        address = self._address.text().strip()
        amount_sat = int(self._amount.value() * COIN)
        fee_rate = self._fee_rate()

        if not validate_address(address):
            self._error.setText("Endereço inválido.")
            return
        if amount_sat <= 0:
            self._error.setText("Valor deve ser maior que zero.")
            return

        fee = estimate_fee(1, 2, fee_rate)
        reply = QMessageBox.question(
            self,
            "Confirmar envio",
            f"Enviar {amount_sat / COIN:.8f} RICK para\n{address}\n\nTaxa: {fee / COIN:.8f} RICK",
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._error.setText("")
            self._btn_send.setEnabled(False)
            self._btn_send.setText("Enviando...")
            self.send_requested.emit(address, amount_sat, fee_rate)

    def on_send_complete(self, success: bool, message: str = "") -> None:
        self._btn_send.setEnabled(True)
        self._btn_send.setText("Enviar")
        if success:
            self._address.clear()
            self._amount.setValue(0)
            self._error.setText("")
        else:
            self._error.setText(message or "Erro ao enviar transação.")

    def set_address_book(self, book: dict) -> None:
        pass
