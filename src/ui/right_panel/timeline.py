"""
Horizontal Timeline Widget
A scrollable list of visual frame thumbnails and placeholders indicating generation status.
"""
from PyQt6.QtWidgets import QWidget, QScrollArea, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap
import os

class ShotCard(QFrame):
    """Clickable UI card representing a single Shot."""
    clicked = pyqtSignal(str)
    
    def __init__(self, shot_id: str, status: str, render_path: str, parent=None):
        super().__init__(parent)
        self.shot_id = shot_id
        self.status = status
        self.render_path = render_path
        self._init_ui()
        
    def _init_ui(self) -> None:
        self.setFixedSize(140, 140)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        # Style based on status
        border_color = "#444444"
        bg_color = "#2b2b2b"
        if self.status == "done":
            border_color = "#2ecc71" # green
        elif self.status == "failed":
            border_color = "#e74c3c" # red
        elif self.status in ["generating", "running"]:
            border_color = "#f1c40f" # orange
            
        self.setStyleSheet(f"""
            ShotCard {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 6px;
            }}
            ShotCard:hover {{
                border: 2px solid #007acc;
                background-color: #353535;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        
        # ID label
        id_label = QLabel(self.shot_id.upper())
        id_label.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 11px;")
        id_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(id_label)
        
        # Thumbnail image
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(124, 75)
        self.thumb_label.setStyleSheet("background-color: #111111; border-radius: 4px;")
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Load image if exists
        frame_file = f"./storage/cache/{self.shot_id}/frame_0000.png"
        if not os.path.exists(frame_file):
            cache_dir = f"./storage/cache/{self.shot_id}"
            if os.path.exists(cache_dir):
                files = [f for f in os.listdir(cache_dir) if f.endswith(".png")]
                if files:
                    frame_file = os.path.join(cache_dir, files[0])
                    
        if os.path.exists(frame_file):
            pixmap = QPixmap(frame_file)
            if not pixmap.isNull():
                self.thumb_label.setPixmap(pixmap.scaled(self.thumb_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.thumb_label.setText("[No Frame]")
            self.thumb_label.setStyleSheet("color: #666666; background-color: #111111; font-size: 10px;")
            
        layout.addWidget(self.thumb_label)
        
        # Status Label
        status_label = QLabel(self.status.upper())
        status_color = "#888888"
        if self.status == "done":
            status_color = "#2ecc71"
        elif self.status == "failed":
            status_color = "#e74c3c"
        elif self.status in ["generating", "running"]:
            status_color = "#f1c40f"
        status_label.setStyleSheet(f"font-weight: bold; color: {status_color}; font-size: 10px;")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)
        
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.shot_id)
            super().mousePressEvent(event)


class TimelineWidget(QWidget):
    """
    Horizontal Timeline Widget
    A scrollable list of visual frame thumbnails and placeholders indicating generation status.
    """
    shot_selected = pyqtSignal(str) # Emitted when a card is clicked
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        title_label = QLabel("Production Sequence Timeline")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        layout.addWidget(title_label)
        
        # Scroll area for cards
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 4px;
            }
        """)
        
        self.scroll_content = QWidget()
        self.scroll_layout = QHBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)
        
    def refresh_timeline(self, world_state) -> None:
        """Queries world_state and rebuilds the timeline list."""
        # Clear existing cards
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
                
        shots = world_state.get_all_shots()
        if not shots:
            empty_label = QLabel("No shots generated yet. Enter a story prompt above and press run.")
            empty_label.setStyleSheet("color: #666666; font-size: 12px; font-style: italic;")
            self.scroll_layout.addWidget(empty_label)
            return
            
        for shot in shots:
            card = ShotCard(shot.shot_id, shot.status, shot.render_path)
            card.clicked.connect(self.shot_selected.emit)
            self.scroll_layout.addWidget(card)

