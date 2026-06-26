"""Deposit screen with QR code."""

from __future__ import annotations

import io

from PySide6.QtCore import Signal
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QListWidget, QPushButton, QVBoxLayout, QWidget

try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False


class DepositScreen(QWidget):
    back_clicked = Signal()
    new_address_clicked = Signal()
    label_changed = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        self._qr_label = QLabel()
        self._qr_label.setAlignment(0x0004)
        self._qr_label.setMinimumSize(200, 200)
        layout.addWidget(self._qr_label, alignment=0x0004)

        self._address_label = QLineEdit()
        self._address_label.setReadOnly(True)
        layout.addWidget(self._address_label)

        row = QHBoxLayout()
        btn_copy = QPushButton("Copiar")
        btn_copy.clicked.connect(self._copy_address)
        btn_new = QPushButton("Gerar novo endereço")
        btn_new.clicked.connect(self.new_address_clicked.emit)
        row.addWidget(btn_copy)
        row.addWidget(btn_new)
        layout.addLayout(row)

        layout.addWidget(QLabel("Label:"))
        self._label_input = QLineEdit()
        self._label_input.textChanged.connect(self._on_label_change)
        layout.addWidget(self._label_input)

        layout.addWidget(QLabel("Endereços:"))
        self._address_list = QListWidget()
        layout.addWidget(self._address_list)

        btn_back = QPushButton("Voltar")
        btn_back.setStyleSheet("background-color: #21262d;")
        btn_back.clicked.connect(self.back_clicked.emit)
        layout.addWidget(btn_back)

        self._current_address = ""

    def set_address(self, address: str, label: str = "") -> None:
        self._current_address = address
        self._address_label.setText(address)
        self._label_input.setText(label)
        self._update_qr(address)

    def set_address_list(self, addresses: list) -> None:
        self._address_list.clear()
        for a in addresses:
            self._address_list.addItem(f"{a.label}: {a.address}")

    def _update_qr(self, address: str) -> None:
        if HAS_QRCODE:
            img = qrcode.make(address)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            pixmap = QPixmap()
            pixmap.loadFromData(buf.getvalue())
            self._qr_label.setPixmap(pixmap.scaled(200, 200))
        else:
            self._qr_label.setText(f"QR: {address[:20]}...")

    def _copy_address(self) -> None:
        QGuiApplication.clipboard().setText(self._current_address)

    def _on_label_change(self, text: str) -> None:
        self.label_changed.emit(self._current_address, text)
