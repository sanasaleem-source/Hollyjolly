"""
Main Window — two-panel PyQt6 desktop UI.
Left 35%: asset browser, prompt, world viewer.
Right 65%: CapCut-style timeline, shot viewer, preview, export.
"""
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QWidget, QVBoxLayout,
    QStatusBar, QMenuBar, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from src.ui.left_panel.asset_browser import AssetBrowser
from src.ui.left_panel.prompt_panel import PromptPanel
from src.ui.left_panel.world_viewer import WorldViewer
from src.ui.right_panel.timeline import Timeline
from src.ui.right_panel.shot_viewer import ShotViewer
from src.ui.right_panel.preview_player import PreviewPlayer

logger = logging.getLogger(__name__)

DARK_STYLE = """
QMainWindow, QWidget { background: #0d0f14; color: #d4d8e8; }
QSplitter::handle { background: #1e2330; width: 2px; }
QMenuBar { background: #13161e; border-bottom: 1px solid #1e2330; }
QMenuBar::item:selected { background: #1e2330; }
QMenu { background: #13161e; border: 1px solid #1e2330; }
QMenu::item:selected { background: #1e2330; }
QStatusBar { background: #13161e; border-top: 1px solid #1e2330; color: #6b7280; font-size: 11px; }
QScrollBar:vertical { background: #13161e; width: 8px; }
QScrollBar::handle:vertical { background: #1e2330; border-radius: 4px; }
"""


class MainWindow(QMainWindow):
    """AI Production Studio — main application window."""

    pipeline_requested     = pyqtSignal(str, str)  # prompt, target_shot
    model_change_requested = pyqtSignal()

    def __init__(self, config: dict, world_state=None, orchestrator=None) -> None:
        super().__init__()
        self.config = config
        self.world_state = world_state
        self.orchestrator = orchestrator

        self.setWindowTitle("AI Production Studio")
        self.setMinimumSize(1280, 720)
        self.setStyleSheet(DARK_STYLE)

        self._build_menu()
        self._build_ui()
        self._build_statusbar()
        self._connect_signals()

        logger.info("Main window initialized")

    def _build_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        file_menu.addAction(QAction("New Project", self))
        file_menu.addAction(QAction("Open Project", self))
        file_menu.addSeparator()
        file_menu.addAction(QAction("Exit", self, triggered=self.close))

        settings_menu = menubar.addMenu("Settings")
        change_model_action = QAction("Change AI Model...", self)
        change_model_action.triggered.connect(self.model_change_requested.emit)
        settings_menu.addAction(change_model_action)

        help_menu = menubar.addMenu("Help")
        help_menu.addAction(QAction("About", self))

    def _build_ui(self) -> None:
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)

        # ── Left Panel ──
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.prompt_panel = PromptPanel()
        self.asset_browser = AssetBrowser()
        self.world_viewer = WorldViewer()

        left_layout.addWidget(self.prompt_panel, stretch=2)
        left_layout.addWidget(self.asset_browser, stretch=3)
        left_layout.addWidget(self.world_viewer, stretch=2)

        # ── Right Panel ──
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.preview_player = PreviewPlayer()
        self.shot_viewer = ShotViewer()
        self.timeline = Timeline()

        right_layout.addWidget(self.preview_player, stretch=3)
        right_layout.addWidget(self.shot_viewer, stretch=2)
        right_layout.addWidget(self.timeline, stretch=2)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([448, 832])  # 35/65 split at 1280px

        self.setCentralWidget(splitter)

    def _build_statusbar(self) -> None:
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        provider = self.config.get("llm_provider", "none") if self.config else "none"
        self.status.showMessage(f"Ready — model: {provider}")

    def _connect_signals(self) -> None:
        self.prompt_panel.submitted.connect(self._on_prompt_submitted)
        self.timeline.shot_selected.connect(self.shot_viewer.load_shot)

    def _on_prompt_submitted(self, prompt: str, target: str) -> None:
        self.status.showMessage(f"Running pipeline — target: {target or 'all shots'}")
        self.pipeline_requested.emit(prompt, target)

    def update_shot_status(self, shot_id: str, status: str) -> None:
        """Called by pipeline worker to update UI."""
        self.timeline.update_shot(shot_id, status)
        self.status.showMessage(f"Shot {shot_id}: {status}")

    def pipeline_complete(self, output_path: str) -> None:
        self.status.showMessage(f"Pipeline complete → {output_path}")
        if output_path:
            self.preview_player.load(output_path)
