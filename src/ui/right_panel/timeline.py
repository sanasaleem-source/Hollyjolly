"""
Timeline — CapCut-style horizontal shot timeline.
Placeholders grey, generating = blue pulse, done = thumbnail, failed = red border.
"""
from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QHBoxLayout, QVBoxLayout,
    QLabel, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QColor, QPainter

STYLE = """
QWidget { background: #0a0c10; }
QScrollArea { border: none; background: #0a0c10; }
"""

SHOT_BASE = """
QFrame {
    border-radius: 6px;
    border: 2px solid #1e2330;
    background: #13161e;
}
QLabel { border: none; background: transparent; color: #6b7280; font-size: 10px; }
"""
SHOT_GENERATING = SHOT_BASE.replace("#1e2330", "#5b6af5")
SHOT_DONE       = SHOT_BASE.replace("#1e2330", "#3ecf8e")
SHOT_FAILED     = SHOT_BASE.replace("#1e2330", "#f06060")


class ShotCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, shot_id: str) -> None:
        super().__init__()
        self.shot_id = shot_id
        self.setFixedSize(QSize(140, 90))
        self.setStyleSheet(SHOT_BASE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.thumb = QLabel()
        self.thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb.setText(shot_id)
        self.thumb.setFixedHeight(60)
        layout.addWidget(self.thumb)

        self.label = QLabel(shot_id)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

    def mousePressEvent(self, event):
        self.clicked.emit(self.shot_id)

    def set_status(self, status: str, frame_path: str = "") -> None:
        if status == "generating":
            self.setStyleSheet(SHOT_GENERATING)
            self.thumb.setText("generating...")
        elif status == "done":
            self.setStyleSheet(SHOT_DONE)
            if frame_path:
                pix = QPixmap(frame_path).scaled(132, 60, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)
                self.thumb.setPixmap(pix)
        elif status == "failed":
            self.setStyleSheet(SHOT_FAILED)
            self.thumb.setText("✕ failed")
        else:
            self.setStyleSheet(SHOT_BASE)
            self.thumb.setText(self.shot_id)


class Timeline(QWidget):
    """Horizontal scrollable shot timeline."""

    shot_selected = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setStyleSheet(STYLE)
        self.cards: dict[str, ShotCard] = {}
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        label = QLabel("TIMELINE")
        label.setStyleSheet("color: #6b7280; font-size: 10px; font-weight: bold;"
                            "letter-spacing: 0.1em; padding: 8px 12px 4px;")
        outer.addWidget(label)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.inner = QWidget()
        self.row = QHBoxLayout(self.inner)
        self.row.setContentsMargins(12, 8, 12, 8)
        self.row.setSpacing(8)
        self.row.addStretch()

        self.scroll.setWidget(self.inner)
        outer.addWidget(self.scroll)

    def load_shots(self, shot_ids: list[str]) -> None:
        """Populate timeline with placeholder cards."""
        # Clear existing
        for card in self.cards.values():
            card.deleteLater()
        self.cards.clear()
        self.row.removeItem(self.row.itemAt(self.row.count() - 1))

        for sid in shot_ids:
            card = ShotCard(sid)
            card.clicked.connect(self.shot_selected)
            self.cards[sid] = card
            self.row.addWidget(card)

        self.row.addStretch()

    def update_shot(self, shot_id: str, status: str, frame_path: str = "") -> None:
        if shot_id in self.cards:
            self.cards[shot_id].set_status(status, frame_path)
