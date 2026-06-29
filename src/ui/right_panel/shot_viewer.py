"""
Shot Viewer — shows frames, prompt, asset versions and validation result for selected shot.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

STYLE = """
QWidget { background: #13161e; border-top: 1px solid #1e2330; }
QLabel.header { color: #6b7280; font-size: 10px; font-weight: bold; letter-spacing: 0.1em; }
QTextEdit { background: #0d0f14; color: #d4d8e8; border: 1px solid #1e2330;
            border-radius: 4px; font-size: 11px; padding: 6px; }
"""


class ShotViewer(QWidget):
    """Detail view for a selected shot."""

    def __init__(self) -> None:
        super().__init__()
        self.setStyleSheet(STYLE)
        self._build()

    def _build(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Frame strip
        frame_col = QVBoxLayout()
        lbl = QLabel("FRAMES")
        lbl.setProperty("class", "header")
        lbl.setStyleSheet("color:#6b7280;font-size:10px;font-weight:bold;")
        frame_col.addWidget(lbl)
        self.frame_scroll = QScrollArea()
        self.frame_scroll.setFixedHeight(80)
        self.frame_inner = QWidget()
        self.frame_row = QHBoxLayout(self.frame_inner)
        self.frame_row.setContentsMargins(0,0,0,0)
        self.frame_row.setSpacing(4)
        self.frame_scroll.setWidget(self.frame_inner)
        self.frame_scroll.setWidgetResizable(True)
        frame_col.addWidget(self.frame_scroll)
        layout.addLayout(frame_col, stretch=2)

        # Info
        info_col = QVBoxLayout()
        info_col.setSpacing(6)

        lbl2 = QLabel("SHOT INFO")
        lbl2.setStyleSheet("color:#6b7280;font-size:10px;font-weight:bold;")
        info_col.addWidget(lbl2)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(80)
        self.info_text.setPlaceholderText("Select a shot to see details...")
        info_col.addWidget(self.info_text)

        layout.addLayout(info_col, stretch=3)

    def load_shot(self, shot_id: str) -> None:
        """Load shot details into the viewer."""
        # Clear frames
        while self.frame_row.count():
            item = self.frame_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.info_text.setPlainText(f"Shot: {shot_id}\nLoading details...")

    def display_shot_data(self, shot_data: dict, frame_paths: list[str]) -> None:
        """Populate with actual shot data and frames."""
        while self.frame_row.count():
            item = self.frame_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for fp in frame_paths[:8]:
            thumb = QLabel()
            pix = QPixmap(fp).scaled(100, 60, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            thumb.setPixmap(pix)
            self.frame_row.addWidget(thumb)

        val = shot_data.get("validation_result", {})
        passed = all(v.get("passed", True) for v in val.values()) if val else True
        status_line = "✅ Validated" if passed else "❌ Validation failed"

        info = (
            f"Shot ID: {shot_data.get('shot_id', 'unknown')}\n"
            f"Scene: {shot_data.get('scene_id', '')}\n"
            f"Status: {shot_data.get('status', '')}\n"
            f"Validation: {status_line}\n"
            f"Repair attempts: {shot_data.get('repair_attempts', 0)}\n"
            f"Description: {shot_data.get('description', '')}"
        )
        self.info_text.setPlainText(info)
