"""Create wallet — show mnemonic."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget


class CreateWalletScreen(QWidget):
    continue_clicked = Signal(str)
    back_clicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._mnemonic = ""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        layout.addWidget(QLabel("Sua frase de recuperação (12 palavras)"))
        layout.addWidget(QLabel("Anote estas palavras em ordem. Nunca compartilhe com ninguém."))

        self._words_display = QTextEdit()
        self._words_display.setReadOnly(True)
        self._words_display.setMinimumHeight(120)
        layout.addWidget(self._words_display)

        btn_copy = QPushButton("Copiar")
        btn_copy.clicked.connect(self._copy_words)
        layout.addWidget(btn_copy)

        btn_continue = QPushButton("Continuar")
        btn_continue.clicked.connect(lambda: self.continue_clicked.emit(self._mnemonic))
        layout.addWidget(btn_continue)

        btn_back = QPushButton("Voltar")
        btn_back.setStyleSheet("background-color: #21262d;")
        btn_back.clicked.connect(self.back_clicked.emit)
        layout.addWidget(btn_back)

    def set_mnemonic(self, mnemonic: str) -> None:
        self._mnemonic = mnemonic
        self._words_display.setText(mnemonic)

    def _copy_words(self) -> None:
        QGuiApplication.clipboard().setText(self._mnemonic)
