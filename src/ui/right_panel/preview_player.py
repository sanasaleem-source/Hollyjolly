"""
Preview Player Widget
Media play-head player mapping composite frames or compiled video outputs.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
import os

class PreviewPlayerWidget(QWidget):
    """
    Preview Player Widget
    Media play-head player mapping composite frames or compiled video outputs.
    """
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.active_shot_id = None
        self._init_ui()
        
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        self.title_label = QLabel("Production Preview Monitor")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        layout.addWidget(self.title_label)
        
        # High-res monitor frame (16:9 aspect ratio placeholder)
        self.monitor = QLabel()
        self.monitor.setMinimumHeight(240)
        self.monitor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.monitor.setStyleSheet("""
            QLabel {
                background-color: #000000;
                border: 1px solid #333333;
                border-radius: 6px;
                color: #888888;
                font-size: 14px;
                font-family: 'JetBrains Mono', monospace;
            }
        """)
        self.monitor.setText("SELECT A SHOT TO PREVIEW RENDER")
        layout.addWidget(self.monitor)
        
        # Media controls layout
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        self.btn_play = QPushButton("◀ ▶ Play Sequence")
        self.btn_play.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b;
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #383838; }
        """)
        controls_layout.addWidget(self.btn_play)
        
        # Slider for timeline scrubber
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #444444;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #007acc;
                width: 12px;
                margin-top: -4px;
                margin-bottom: -4px;
                border-radius: 6px;
            }
        """)
        controls_layout.addWidget(self.slider)
        
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: #888888; font-size: 11px; font-family: 'JetBrains Mono', monospace;")
        controls_layout.addWidget(self.time_label)
        
        layout.addLayout(controls_layout)
        
    def load_shot_preview(self, shot_id: str) -> None:
        """Loads and scales the selected shot's rendered frame image."""
        self.active_shot_id = shot_id
        self.title_label.setText(f"Preview Monitor - Active: {shot_id.upper()}")
        
        frame_file = f"./storage/cache/{shot_id}/frame_0000.png"
        
        # Look for fallback PNGs in cache folder if frame_0000 is not directly there
        if not os.path.exists(frame_file):
            cache_dir = f"./storage/cache/{shot_id}"
            if os.path.exists(cache_dir):
                files = [f for f in os.listdir(cache_dir) if f.endswith(".png")]
                if files:
                    frame_file = os.path.join(cache_dir, files[0])
                    
        if os.path.exists(frame_file):
            pixmap = QPixmap(frame_file)
            if not pixmap.isNull():
                # Scale nicely preserving aspect ratio
                scaled_pixmap = pixmap.scaled(self.monitor.width(), self.monitor.height(), 
                                              Qt.AspectRatioMode.KeepAspectRatio, 
                                              Qt.TransformationMode.SmoothTransformation)
                self.monitor.setPixmap(scaled_pixmap)
                self.monitor.setStyleSheet("background-color: #000000; border: 1px solid #333333; border-radius: 6px;")
            else:
                self.monitor.setText(f"Corrupted render frame file found for {shot_id.upper()}")
        else:
            self.monitor.setText(f"NO RENDER FRAME FILE FOUND FOR {shot_id.upper()}\n({frame_file})")
            self.monitor.setStyleSheet("background-color: #111111; color: #666666; border: 1px solid #333333; border-radius: 6px;")

