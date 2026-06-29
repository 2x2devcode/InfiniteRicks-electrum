"""Settings screen."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget

from infinitericks_wallet import __version__
from infinitericks_wallet.config.chainparams import EXPLORER_URL, WEBSITE_URL


class SettingsScreen(QWidget):
    back_clicked = Signal()
    delete_wallet = Signal()
    change_password = Signal()
    backup_wallet = Signal()
    logout = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Configurações"))
        self._version = QLabel(f"Versão: {__version__}")
        layout.addWidget(self._version)

        self._network = QLabel("Status: —")
        layout.addWidget(self._network)
        self._height = QLabel("Altura do bloco: —")
        layout.addWidget(self._height)
        self._server = QLabel("Servidor: —")
        layout.addWidget(self._server)

        layout.addWidget(QLabel(f"Site: {WEBSITE_URL}"))
        layout.addWidget(QLabel(f"Explorer: {EXPLORER_URL}"))

        btn_backup = QPushButton("Backup")
        btn_backup.clicked.connect(self.backup_wallet.emit)
        layout.addWidget(btn_backup)

        btn_password = QPushButton("Alterar senha")
        btn_password.clicked.connect(self.change_password.emit)
        layout.addWidget(btn_password)

        btn_delete = QPushButton("Excluir carteira")
        btn_delete.setStyleSheet("background-color: #da3633;")
        btn_delete.clicked.connect(self._confirm_delete)
        layout.addWidget(btn_delete)

        btn_logout = QPushButton("Sair")
        btn_logout.setStyleSheet("background-color: #21262d;")
        btn_logout.clicked.connect(self.logout.emit)
        layout.addWidget(btn_logout)

        btn_back = QPushButton("Voltar")
        btn_back.clicked.connect(self.back_clicked.emit)
        layout.addWidget(btn_back)

    def update_status(self, connected: bool, height: int, server: str, error: str = "") -> None:
        self._network.setText(f"Status: {'Conectado' if connected else 'Desconectado'}")
        self._height.setText(f"Altura do bloco: {height:,}" if height else "Altura do bloco: —")
        self._server.setText(f"Servidor: {server}")
        if error and not connected:
            self._server.setToolTip(f"Último erro: {error}")
        else:
            self._server.setToolTip("")

    def _confirm_delete(self) -> None:
        reply = QMessageBox.warning(
            self, "Excluir carteira",
            "Tem certeza? Esta ação é irreversível. Faça backup da seed antes.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_wallet.emit()
