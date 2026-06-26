"""Password setup screen."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget


class PasswordScreen(QWidget):
    password_set = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Defina uma senha para criptografar sua carteira"))
        layout.addWidget(QLabel("Mínimo 8 caracteres. Nenhuma chave privada sairá do dispositivo."))

        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self._password)

        self._confirm = QLineEdit()
        self._confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm.setPlaceholderText("Confirmar senha")
        layout.addWidget(self._confirm)

        self._error = QLabel("")
        self._error.setStyleSheet("color: #f85149;")
        layout.addWidget(self._error)

        btn = QPushButton("Continuar")
        btn.clicked.connect(self._submit)
        layout.addWidget(btn)

    def _submit(self) -> None:
        p1, p2 = self._password.text(), self._confirm.text()
        if len(p1) < 8:
            self._error.setText("Senha muito curta.")
            return
        if p1 != p2:
            self._error.setText("Senhas não coincidem.")
            return
        self.password_set.emit(p1)
