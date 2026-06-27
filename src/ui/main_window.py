"""
MainWindow UI Class
Creates the dual-panel desktop workspace.
"""

import logging
from typing import Dict, Any

try:
    from PyQt6.QtWidgets import QMainWindow, QSplitter, QWidget, QHBoxLayout, QStatusBar
    from PyQt6.QtCore import Qt
except ImportError:
    # Safe fallback if running without PyQt6 installed
    class QMainWindow: pass
    class QWidget: pass
    Qt = None

class MainWindow(QMainWindow):
    """Primary window container styling 35% Control panel, 65% Timeline panel."""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__()
        self.config = config
        self.logger = logging.getLogger("MainWindow")
        self._init_window()

    def _init_window(self) -> None:
        self.setWindowTitle("AI Production Studio - V1 Pro")
        self.resize(1280, 720)
        
        # Dark visual theme styling
        self.setStyleSheet("""
            QMainWindow { background-color: #1a1a1a; }
            QSplitter::handle { background-color: #333333; }
            QStatusBar { background-color: #111111; color: #888888; }
        """)
        
        # Add status bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready.")
        
        # Splitter layout
        # (Instantiated with panels in subsequent phases)
        self.logger.info("Main Window initialized.")
logging = logging
Dict = Dict
Any = Any
MainWindow = MainWindow
