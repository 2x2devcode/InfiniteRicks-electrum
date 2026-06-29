"""Main home screen."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from infinitericks_wallet import __app_name__
from infinitericks_wallet.config.chainparams import COIN, WEBSITE_URL


class HomeScreen(QWidget):
    deposit_clicked = Signal()
    send_clicked = Signal()
    transactions_clicked = Signal()
    settings_clicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        logo = QLabel("∞ RICK")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
        logo.setStyleSheet("color: #58a6ff;")
        layout.addWidget(logo)

        title = QLabel(__app_name__)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; color: #8b949e;")
        layout.addWidget(title)

        self._balance = QLabel("0.00000000 RICK")
        self._balance.setObjectName("balance")
        self._balance.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._balance.setStyleSheet("font-size: 28px; font-weight: bold; color: #3fb950;")
        layout.addWidget(self._balance)

        self._fiat = QLabel("≈ — (conversão preparada)")
        self._fiat.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._fiat.setStyleSheet("color: #8b949e;")
        layout.addWidget(self._fiat)

        btn_grid = QGridLayout()
        for i, (text, slot) in enumerate([
            ("Deposit Coins", self.deposit_clicked),
            ("Send Coins", self.send_clicked),
            ("Transactions", self.transactions_clicked),
            ("Settings", self.settings_clicked),
        ]):
            btn = QPushButton(text)
            btn.setMinimumHeight(48)
            btn.clicked.connect(slot.emit)
            btn_grid.addWidget(btn, i // 2, i % 2)
        layout.addLayout(btn_grid)

        layout.addWidget(QLabel("Últimas transações"))
        self._tx_list = QListWidget()
        self._tx_list.setMaximumHeight(150)
        layout.addWidget(self._tx_list)

        status_row = QHBoxLayout()
        self._network_status = QLabel("🔴 No Connection")
        self._block_height = QLabel("Block: —")
        status_row.addWidget(self._network_status)
        status_row.addStretch()
        status_row.addWidget(self._block_height)
        layout.addLayout(status_row)

        link = QLabel(f'<a href="{WEBSITE_URL}">{WEBSITE_URL}</a>')
        link.setOpenExternalLinks(True)
        link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(link)

    def update_balance(self, satoshis: int) -> None:
        rick = satoshis / COIN
        self._balance.setText(f"{rick:.8f} RICK")

    def update_network(self, connected: bool, height: int, error: str = "") -> None:
        if connected:
            self._network_status.setText("🟢 Active Mainnet Network")
            self._network_status.setStyleSheet("color: #3fb950;")
        elif error:
            self._network_status.setText("🔴 No Connection (servidor SPV offline)")
            self._network_status.setStyleSheet("color: #f85149;")
            self._network_status.setToolTip(error)
        else:
            self._network_status.setText("🟡 Connecting...")
            self._network_status.setStyleSheet("color: #d29922;")
            self._network_status.setToolTip("")
        self._block_height.setText(f"Block: {height:,}" if height else "Block: —")

    def update_transactions(self, items: list) -> None:
        self._tx_list.clear()
        if not items:
            self._tx_list.addItem("Nenhuma transação encontrada.")
        else:
            for item in items:
                value = item.value / COIN
                conf = item.confirmations
                self._tx_list.addItem(f"{item.tx_hash[:16]}... | {value:+.8f} RICK | {conf} conf")
