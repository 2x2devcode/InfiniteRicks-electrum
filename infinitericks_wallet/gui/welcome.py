"""Welcome screen — create or import wallet."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from infinitericks_wallet import __app_name__


class WelcomeScreen(QWidget):
    create_clicked = Signal()
    import_clicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.addStretch()

        title = QLabel(__app_name__)
        title.setObjectName("title")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #58a6ff;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Carteira leve SPV para InfiniteRicks")
        subtitle.setStyleSheet("font-size: 16px; color: #8b949e;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(40)

        btn_create = QPushButton("Criar Carteira")
        btn_create.setMinimumHeight(50)
        btn_create.clicked.connect(self.create_clicked.emit)

        btn_import = QPushButton("Importar Carteira")
        btn_import.setProperty("class", "secondary")
        btn_import.setStyleSheet("background-color: #21262d; border: 1px solid #30363d; border-radius: 8px; padding: 12px;")
        btn_import.setMinimumHeight(50)
        btn_import.clicked.connect(self.import_clicked.emit)

        layout.addWidget(btn_create)
        layout.addWidget(btn_import)
        layout.addStretch()
