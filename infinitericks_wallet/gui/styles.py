"""Application stylesheet."""

STYLE = """
QMainWindow, QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Segoe UI', 'Roboto', sans-serif;
    font-size: 14px;
}
QPushButton {
    background-color: #238636;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-weight: bold;
    min-height: 20px;
}
QPushButton:hover { background-color: #2ea043; }
QPushButton:pressed { background-color: #196c2e; }
QPushButton:disabled { background-color: #21262d; color: #484f58; }
QPushButton.secondary {
    background-color: #21262d;
    border: 1px solid #30363d;
}
QPushButton.secondary:hover { background-color: #30363d; }
QPushButton.danger { background-color: #da3633; }
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 10px;
    color: #e6edf3;
}
QLabel.title { font-size: 24px; font-weight: bold; color: #58a6ff; }
QLabel.subtitle { font-size: 16px; color: #8b949e; }
QLabel.balance { font-size: 32px; font-weight: bold; color: #3fb950; }
QListWidget {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
}
QListWidget::item { padding: 8px; border-bottom: 1px solid #21262d; }
QListWidget::item:selected { background-color: #1f6feb; }
QGroupBox {
    border: 1px solid #30363d;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
}
"""
