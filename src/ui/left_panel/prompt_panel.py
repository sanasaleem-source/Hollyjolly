"""
Prompt Panel — story prompt input with shot targeting and submit.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QComboBox, QLabel
)
from PyQt6.QtCore import pyqtSignal

PANEL_STYLE = """
QWidget { background: #13161e; border-bottom: 1px solid #1e2330; }
QTextEdit {
    background: #0d0f14; color: #d4d8e8; border: 1px solid #1e2330;
    border-radius: 6px; padding: 10px; font-size: 13px;
}
QPushButton {
    background: #5b6af5; color: white; border: none;
    border-radius: 6px; padding: 10px 20px; font-weight: bold; font-size: 13px;
}
QPushButton:hover { background: #6b7aff; }
QPushButton:pressed { background: #4a59e4; }
QComboBox {
    background: #0d0f14; color: #d4d8e8; border: 1px solid #1e2330;
    border-radius: 4px; padding: 6px; font-size: 12px;
}
QLabel { color: #6b7280; font-size: 11px; font-weight: bold;
         letter-spacing: 0.08em; padding: 10px 12px 4px; }
"""


class PromptPanel(QWidget):
    """Story prompt input with shot targeting."""

    submitted = pyqtSignal(str, str)  # prompt text, target shot id

    def __init__(self) -> None:
        super().__init__()
        self.setStyleSheet(PANEL_STYLE)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(6)

        layout.addWidget(QLabel("STORY PROMPT"))

        self.text_input = QTextEdit()
        placeholder_text = (
            "Describe your story or scene...\n\n"
            "Example: A detective in 1940s rain-soaked Chicago "
            "discovers a clue at an abandoned warehouse."
        )
        self.text_input.setPlaceholderText(placeholder_text)
        self.text_input.setMinimumHeight(100)
        layout.addWidget(self.text_input)

        layout.addWidget(QLabel("TARGET"))

        bottom = QHBoxLayout()
        self.target_selector = QComboBox()
        self.target_selector.addItems(["All shots", "Scene 1", "Shot 1-01"])
        bottom.addWidget(self.target_selector, stretch=1)

        self.submit_btn = QPushButton("Generate \u25B6")
        self.submit_btn.clicked.connect(self._on_submit)
        bottom.addWidget(self.submit_btn)

        layout.addLayout(bottom)

    def _on_submit(self) -> None:
        prompt = self.text_input.toPlainText().strip()
        target = self.target_selector.currentText()
        if target == "All shots":
            target = ""
        if prompt:
            self.submitted.emit(prompt, target)

    def set_targets(self, shots: list[str]) -> None:
        """Update the target dropdown with current shot list."""
        self.target_selector.clear()
        self.target_selector.addItem("All shots")
        self.target_selector.addItems(shots)
