"""Transactions list screen."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QListWidget, QPushButton, QTextEdit, QVBoxLayout, QWidget

from infinitericks_wallet.config.chainparams import COIN


class TransactionsScreen(QWidget):
    back_clicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Transações"))

        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._show_detail)
        layout.addWidget(self._list)

        self._detail = QTextEdit()
        self._detail.setReadOnly(True)
        self._detail.setMaximumHeight(200)
        layout.addWidget(self._detail)

        btn_back = QPushButton("Voltar")
        btn_back.setStyleSheet("background-color: #21262d;")
        btn_back.clicked.connect(self.back_clicked.emit)
        layout.addWidget(btn_back)

        self._history: list = []

    def set_history(self, history: list) -> None:
        self._history = sorted(history, key=lambda h: h.height, reverse=True)
        self._list.clear()
        for item in self._history:
            value = item.value / COIN
            self._list.addItem(
                f"{'+' if value >= 0 else ''}{value:.8f} RICK | {item.confirmations} conf | h={item.height}"
            )

    def _show_detail(self, row: int) -> None:
        if row < 0 or row >= len(self._history):
            return
        item = self._history[row]
        self._detail.setText(
            f"Hash: {item.tx_hash}\n"
            f"Valor: {item.value / COIN:.8f} RICK\n"
            f"Confirmações: {item.confirmations}\n"
            f"Altura: {item.height}\n"
            f"Data: {item.timestamp}\n"
            f"Endereços: {', '.join(item.addresses)}"
        )
