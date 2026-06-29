"""
Preview Player — plays the final assembled video output.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont

STYLE = """
QWidget { background: #0d0f14; border-bottom: 1px solid #1e2330; }
QLabel#placeholder {
    color: #2a2e3e; font-size: 13px;
    border: 2px dashed #1e2330; border-radius: 8px;
}
QPushButton {
    background: #3ecf8e; color: #0a0c10; border: none;
    border-radius: 6px; padding: 8px 20px; font-weight: bold; font-size: 12px;
}
QPushButton:hover { background: #4edfae; }
QPushButton#export_btn {
    background: #5b6af5;
    color: white;
}
QPushButton#export_btn:hover { background: #6b7aff; }
"""


class PreviewPlayer(QWidget):
    """Video preview area with export button."""

    def __init__(self) -> None:
        super().__init__()
        self.setStyleSheet(STYLE)
        self.video_path = ""
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 8)
        layout.setSpacing(8)

        # Preview area
        self.placeholder = QLabel("Preview will appear here after generation")
        self.placeholder.setObjectName("placeholder")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setMinimumHeight(200)
        layout.addWidget(self.placeholder, stretch=1)

        # Controls
        controls = QHBoxLayout()

        try:
            from PyQt6.QtMultimediaWidgets import QVideoWidget
            from PyQt6.QtMultimedia import QMediaPlayer
            self.player = QMediaPlayer()
            self.video_widget = QVideoWidget()
            self.player.setVideoOutput(self.video_widget)
            layout.addWidget(self.video_widget, stretch=1)
            self.video_widget.hide()

            self.play_btn = QPushButton("▶ Play")
            self.play_btn.clicked.connect(self.player.play)
            controls.addWidget(self.play_btn)
        except ImportError:
            self.player = None
            lbl = QLabel("Install PyQt6-Multimedia for video preview")
            lbl.setStyleSheet("color: #6b7280; font-size: 11px;")
            controls.addWidget(lbl)

        controls.addStretch()

        self.export_btn = QPushButton("Export Video")
        self.export_btn.setObjectName("export_btn")
        controls.addWidget(self.export_btn)

        layout.addLayout(controls)

    def load(self, video_path: str) -> None:
        """Load and show a video file."""
        self.video_path = video_path
        if self.player:
            self.player.setSource(QUrl.fromLocalFile(video_path))
            self.placeholder.hide()
            self.video_widget.show()
            self.player.play()
