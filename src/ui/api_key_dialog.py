"""
API Key Dialog — shown on first launch if no Gemini key is configured.
User enters their key once, it is saved to config.yaml.
"""
import yaml
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

STYLE = """
QDialog { background: #0d0f14; }
QLabel { color: #d4d8e8; }
QLabel#title { font-size: 16px; font-weight: bold; color: white; }
QLabel#sub   { font-size: 12px; color: #6b7280; }
QLabel#link  { font-size: 11px; color: #5b6af5; }
QLineEdit {
    background: #13161e; color: #d4d8e8;
    border: 1px solid #1e2330; border-radius: 6px;
    padding: 10px 12px; font-size: 13px;
}
QLineEdit:focus { border-color: #5b6af5; }
QPushButton {
    background: #5b6af5; color: white; border: none;
    border-radius: 6px; padding: 10px 24px;
    font-weight: bold; font-size: 13px;
}
QPushButton:hover { background: #6b7aff; }
QPushButton#skip_btn {
    background: transparent; color: #6b7280;
    border: 1px solid #1e2330;
}
QPushButton#skip_btn:hover { color: #d4d8e8; border-color: #d4d8e8; }
QFrame#divider { background: #1e2330; }
"""


class APIKeyDialog(QDialog):
    """First-run dialog to collect Gemini API key."""

    def __init__(self, config: dict) -> None:
        super().__init__()
        self.config = dict(config)
        self.setWindowTitle("AI Production Studio — Setup")
        self.setFixedSize(480, 360)
        self.setStyleSheet(STYLE)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 28)
        layout.setSpacing(0)

        # Logo / title
        title = QLabel("AI Production Studio")
        title.setObjectName("title")
        layout.addWidget(title)
        layout.addSpacing(6)

        sub = QLabel("Enter your Google AI Studio API key to get started.
This is saved locally — never sent anywhere else.")
        sub.setObjectName("sub")
        sub.setWordWrap(True)
        layout.addWidget(sub)
        layout.addSpacing(24)

        # Key input
        key_label = QLabel("Gemini API Key")
        key_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #6b7280; letter-spacing: 0.08em;")
        layout.addWidget(key_label)
        layout.addSpacing(6)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("AIza...")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.key_input)
        layout.addSpacing(8)

        link = QLabel("Get a free key at aistudio.google.com/app/apikey")
        link.setObjectName("link")
        layout.addWidget(link)

        layout.addStretch()

        # Divider
        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFixedHeight(1)
        layout.addWidget(divider)
        layout.addSpacing(16)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        skip_btn = QPushButton("Skip for now")
        skip_btn.setObjectName("skip_btn")
        skip_btn.clicked.connect(self.reject)
        btn_row.addWidget(skip_btn)

        btn_row.addStretch()

        save_btn = QPushButton("Save & Continue")
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _on_save(self) -> None:
        key = self.key_input.text().strip()
        if key:
            self.config["gemini_api_key"] = key
            self.accept()

    def get_updated_config(self) -> dict:
        return self.config
