"""Import wallet screen."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QTextEdit, QVBoxLayout, QWidget

from infinitericks_wallet.wallet.mnemonic import validate_mnemonic


class ImportWalletScreen(QWidget):
    import_confirmed = Signal(str, str)
    back_clicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        layout.addWidget(QLabel("Importar Carteira"))
        layout.addWidget(QLabel("Digite suas 12 palavras de recuperação:"))

        self._mnemonic_input = QTextEdit()
        self._mnemonic_input.setPlaceholderText("palavra1 palavra2 palavra3 ...")
        self._mnemonic_input.setMinimumHeight(100)
        layout.addWidget(self._mnemonic_input)

        layout.addWidget(QLabel("Senha da carteira:"))
        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self._password)

        layout.addWidget(QLabel("Confirmar senha:"))
        self._password_confirm = QLineEdit()
        self._password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self._password_confirm)

        self._error = QLabel("")
        self._error.setStyleSheet("color: #f85149;")
        layout.addWidget(self._error)

        btn_import = QPushButton("Criar Carteira")
        btn_import.clicked.connect(self._do_import)
        layout.addWidget(btn_import)

        btn_back = QPushButton("Voltar")
        btn_back.setStyleSheet("background-color: #21262d;")
        btn_back.clicked.connect(self.back_clicked.emit)
        layout.addWidget(btn_back)

    def _do_import(self) -> None:
        mnemonic = self._mnemonic_input.toPlainText().strip()
        password = self._password.text()
        confirm = self._password_confirm.text()

        if not validate_mnemonic(mnemonic):
            self._error.setText("Seed inválida. Verifique as 12 palavras.")
            return
        if len(password) < 8:
            self._error.setText("A senha deve ter pelo menos 8 caracteres.")
            return
        if password != confirm:
            self._error.setText("As senhas não coincidem.")
            return
        self._error.setText("")
        self.import_confirmed.emit(mnemonic, password)
