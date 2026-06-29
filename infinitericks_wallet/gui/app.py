"""Main application window and navigation."""

from __future__ import annotations

import logging
import sys
import threading
from typing import Optional

from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QLineEdit, QMainWindow, QMessageBox, QStackedWidget, QVBoxLayout, QWidget

from infinitericks_wallet.gui.create_wallet import CreateWalletScreen
from infinitericks_wallet.gui.deposit import DepositScreen
from infinitericks_wallet.gui.home import HomeScreen
from infinitericks_wallet.gui.import_wallet import ImportWalletScreen
from infinitericks_wallet.gui.password import PasswordScreen
from infinitericks_wallet.gui.send import SendScreen
from infinitericks_wallet.gui.settings import SettingsScreen
from infinitericks_wallet.gui.styles import STYLE
from infinitericks_wallet.gui.transactions import TransactionsScreen
from infinitericks_wallet.gui.verify_seed import VerifySeedScreen
from infinitericks_wallet.gui.welcome import WelcomeScreen
from infinitericks_wallet.spv.sync_manager import SyncManager
from infinitericks_wallet.storage.encrypted_store import EncryptedStore
from infinitericks_wallet.wallet.wallet import Wallet

logger = logging.getLogger(__name__)

SCREEN_WELCOME = 0
SCREEN_CREATE = 1
SCREEN_VERIFY = 2
SCREEN_PASSWORD = 3
SCREEN_IMPORT = 4
SCREEN_HOME = 5
SCREEN_DEPOSIT = 6
SCREEN_SEND = 7
SCREEN_TRANSACTIONS = 8
SCREEN_SETTINGS = 9
SCREEN_UNLOCK = 10


class UnlockScreen(QWidget):
    def __init__(self, store: EncryptedStore, on_unlocked) -> None:
        super().__init__()
        from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton

        self._store = store
        self._on_unlocked = on_unlocked
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Desbloquear carteira"))
        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self._password)
        self._error = QLabel("")
        self._error.setStyleSheet("color: #f85149;")
        layout.addWidget(self._error)
        btn = QPushButton("Desbloquear")
        btn.clicked.connect(self._unlock)
        layout.addWidget(btn)

    def _unlock(self) -> None:
        try:
            wallet = self._store.load(self._password.text())
            self._on_unlocked(wallet, self._password.text())
        except Exception:
            self._error.setText("Senha incorreta ou arquivo corrompido.")


class WalletApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("InfiniteRicks Electrum Wallet")
        self.setMinimumSize(420, 700)
        self.resize(480, 800)

        self._store = EncryptedStore()
        self._wallet: Optional[Wallet] = None
        self._password: str = ""
        self._pending_mnemonic: str = ""
        self._sync: Optional[SyncManager] = None

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._welcome = WelcomeScreen()
        self._create = CreateWalletScreen()
        self._verify = VerifySeedScreen()
        self._password_screen = PasswordScreen()
        self._import = ImportWalletScreen()
        self._home = HomeScreen()
        self._deposit = DepositScreen()
        self._send = SendScreen()
        self._transactions = TransactionsScreen()
        self._settings = SettingsScreen()
        self._unlock = UnlockScreen(self._store, self._on_wallet_unlocked)

        for w in [
            self._welcome, self._create, self._verify, self._password_screen,
            self._import, self._home, self._deposit, self._send,
            self._transactions, self._settings, self._unlock,
        ]:
            self._stack.addWidget(w)

        self._connect_signals()

        if self._store.exists:
            self._stack.setCurrentIndex(SCREEN_UNLOCK)
        else:
            self._stack.setCurrentIndex(SCREEN_WELCOME)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_ui)
        self._refresh_timer.start(5000)

    def _connect_signals(self) -> None:
        self._welcome.create_clicked.connect(self._start_create)
        self._welcome.import_clicked.connect(lambda: self._stack.setCurrentIndex(SCREEN_IMPORT))
        self._create.continue_clicked.connect(self._go_verify)
        self._create.back_clicked.connect(lambda: self._stack.setCurrentIndex(SCREEN_WELCOME))
        self._verify.verified.connect(lambda: self._stack.setCurrentIndex(SCREEN_PASSWORD))
        self._verify.restart.connect(self._start_create)
        self._password_screen.password_set.connect(self._finish_create)
        self._import.import_confirmed.connect(self._finish_import)
        self._import.back_clicked.connect(lambda: self._stack.setCurrentIndex(SCREEN_WELCOME))
        self._home.deposit_clicked.connect(self._show_deposit)
        self._home.send_clicked.connect(lambda: self._stack.setCurrentIndex(SCREEN_SEND))
        self._home.transactions_clicked.connect(self._show_transactions)
        self._home.settings_clicked.connect(self._show_settings)
        self._deposit.back_clicked.connect(lambda: self._stack.setCurrentIndex(SCREEN_HOME))
        self._deposit.new_address_clicked.connect(self._new_address)
        self._send.back_clicked.connect(lambda: self._stack.setCurrentIndex(SCREEN_HOME))
        self._send.send_requested.connect(self._do_send)
        self._transactions.back_clicked.connect(lambda: self._stack.setCurrentIndex(SCREEN_HOME))
        self._settings.back_clicked.connect(lambda: self._stack.setCurrentIndex(SCREEN_HOME))
        self._settings.delete_wallet.connect(self._delete_wallet)
        self._settings.change_password.connect(self._change_password)
        self._settings.backup_wallet.connect(self._backup_wallet)
        self._settings.logout.connect(self._logout)

    def _start_create(self) -> None:
        wallet, mnemonic = Wallet.create_new()
        self._pending_mnemonic = mnemonic
        self._wallet = wallet
        self._create.set_mnemonic(mnemonic)
        self._stack.setCurrentIndex(SCREEN_CREATE)

    def _go_verify(self, mnemonic: str) -> None:
        self._pending_mnemonic = mnemonic
        self._verify.setup(mnemonic)
        self._stack.setCurrentIndex(SCREEN_VERIFY)

    def _finish_create(self, password: str) -> None:
        if not self._wallet:
            self._wallet = Wallet()
            self._wallet.load_from_mnemonic(self._pending_mnemonic)
        self._password = password
        self._store.save(self._wallet, password)
        self._start_sync()
        self._stack.setCurrentIndex(SCREEN_HOME)
        self._refresh_ui()

    def _finish_import(self, mnemonic: str, password: str) -> None:
        self._wallet = Wallet()
        self._wallet.load_from_mnemonic(mnemonic)
        self._password = password
        self._store.save(self._wallet, password)
        self._start_sync()
        self._stack.setCurrentIndex(SCREEN_HOME)
        self._refresh_ui()

    def _on_wallet_unlocked(self, wallet: Wallet, password: str) -> None:
        self._wallet = wallet
        self._password = password
        self._start_sync()
        self._stack.setCurrentIndex(SCREEN_HOME)
        self._refresh_ui()

    def _start_sync(self) -> None:
        if not self._wallet:
            return
        if self._sync:
            self._sync.stop()
        self._sync = SyncManager(self._wallet, on_update=self._schedule_refresh)
        self._sync.start()

    def _schedule_refresh(self) -> None:
        """Queue UI refresh on the Qt main thread (sync runs in background)."""
        QTimer.singleShot(0, self._refresh_ui)

    def _refresh_ui(self) -> None:
        if not self._wallet:
            return
        connected = self._sync.connected if self._sync else False
        height = self._sync.tip_height if self._sync else 0
        self._home.update_balance(self._wallet.balance())
        self._home.update_network(connected, height)
        self._home.update_transactions(self._wallet.recent_history())
        if self._stack.currentIndex() == SCREEN_SETTINGS and self._sync:
            self._settings.update_status(connected, height, self._sync.client.current_server)

    def _show_deposit(self) -> None:
        if self._wallet:
            addr = self._wallet.get_receive_address()
            self._deposit.set_address(addr.address, addr.label)
            self._deposit.set_address_list(self._wallet.addresses)
        self._stack.setCurrentIndex(SCREEN_DEPOSIT)

    def _new_address(self) -> None:
        if self._wallet:
            addr = self._wallet.generate_address()
            self._deposit.set_address(addr.address, addr.label)
            self._deposit.set_address_list(self._wallet.addresses)
            self._save_wallet()

    def _show_transactions(self) -> None:
        if self._wallet:
            self._transactions.set_history(self._wallet.history)
        self._stack.setCurrentIndex(SCREEN_TRANSACTIONS)

    def _show_settings(self) -> None:
        if self._sync:
            self._settings.update_status(self._sync.connected, self._sync.tip_height, self._sync.client.current_server)
        self._stack.setCurrentIndex(SCREEN_SETTINGS)

    def _do_send(self, address: str, amount: int, fee_rate: int) -> None:
        if not self._wallet or not self._sync:
            self._send.on_send_complete(False, "Carteira não sincronizada.")
            return
        wallet = self._wallet
        sync = self._sync

        def _broadcast() -> None:
            try:
                tx = wallet.create_send_tx(address, amount, fee_rate)
                raw = tx.serialize().hex()
                txid = sync.broadcast_transaction(raw)
            except Exception as exc:
                QTimer.singleShot(0, lambda: self._send.on_send_complete(False, str(exc)))
                return

            def _finish() -> None:
                self._save_wallet()
                self._send.on_send_complete(True)
                QMessageBox.information(self, "Sucesso", f"Transação enviada!\n{txid}")
                self._stack.setCurrentIndex(SCREEN_HOME)

            QTimer.singleShot(0, _finish)

        threading.Thread(target=_broadcast, daemon=True).start()

    def _save_wallet(self) -> None:
        if self._wallet and self._password:
            self._store.save(self._wallet, self._password)

    def _delete_wallet(self) -> None:
        if self._sync:
            self._sync.stop()
        self._store.delete()
        self._wallet = None
        self._password = ""
        self._stack.setCurrentIndex(SCREEN_WELCOME)

    def _change_password(self) -> None:
        from PySide6.QtWidgets import QInputDialog
        old, ok = QInputDialog.getText(self, "Senha atual", "Senha:", echo=QLineEdit.EchoMode.Password)
        if not ok:
            return
        new, ok = QInputDialog.getText(self, "Nova senha", "Nova senha:", echo=QLineEdit.EchoMode.Password)
        if not ok or len(new) < 8:
            return
        try:
            self._store.change_password(old, new)
            self._password = new
            QMessageBox.information(self, "Sucesso", "Senha alterada.")
        except Exception:
            QMessageBox.warning(self, "Erro", "Senha atual incorreta.")

    def _backup_wallet(self) -> None:
        if self._wallet and self._wallet.mnemonic:
            QGuiApplication.clipboard().setText(self._wallet.mnemonic)
            QMessageBox.information(self, "Backup", "Seed copiada para a área de transferência.\nGuarde em local seguro!")

    def _logout(self) -> None:
        if self._sync:
            self._sync.stop()
        self._wallet = None
        self._password = ""
        self._stack.setCurrentIndex(SCREEN_UNLOCK if self._store.exists else SCREEN_WELCOME)

    def closeEvent(self, event) -> None:
        if self._sync:
            self._sync.stop()
        if self._wallet and self._password:
            self._save_wallet()
        event.accept()


def run_app() -> int:
    logging.basicConfig(level=logging.INFO)
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    window = WalletApp()
    window.show()
    return app.exec()
