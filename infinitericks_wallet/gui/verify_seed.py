"""Seed verification screen."""

from __future__ import annotations

import random
from typing import List

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget


class VerifySeedScreen(QWidget):
    verified = Signal()
    restart = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._words: List[str] = []
        self._positions: List[int] = []
        self._inputs: List[QLineEdit] = []
        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: #f85149;")

        self._layout = QVBoxLayout(self)
        self._fields_layout = QVBoxLayout()
        self._layout.addWidget(QLabel("Verificação da seed"))
        self._layout.addWidget(QLabel("Informe as palavras solicitadas:"))
        self._layout.addLayout(self._fields_layout)
        self._layout.addWidget(self._error_label)

        btn_verify = QPushButton("Verificar")
        btn_verify.clicked.connect(self._verify)
        self._layout.addWidget(btn_verify)

        btn_restart = QPushButton("Começar novamente")
        btn_restart.setStyleSheet("background-color: #da3633;")
        btn_restart.clicked.connect(self.restart.emit)
        self._layout.addWidget(btn_restart)

    def setup(self, mnemonic: str) -> None:
        self._words = mnemonic.strip().split()
        self._positions = sorted(random.sample(range(12), 3))
        self._error_label.setText("")

        while self._fields_layout.count():
            item = self._fields_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._inputs.clear()

        for pos in self._positions:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"Palavra #{pos + 1}:"))
            inp = QLineEdit()
            inp.setPlaceholderText(f"Digite a palavra {pos + 1}")
            self._inputs.append(inp)
            row.addWidget(inp)
            container = QWidget()
            container.setLayout(row)
            self._fields_layout.addWidget(container)

    def _verify(self) -> None:
        for i, pos in enumerate(self._positions):
            if self._inputs[i].text().strip().lower() != self._words[pos].lower():
                self._error_label.setText("Palavra incorreta. Verifique e tente novamente.")
                return
        self._error_label.setText("")
        self.verified.emit()
