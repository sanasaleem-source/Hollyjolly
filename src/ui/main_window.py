"""
MainWindow UI Class
Creates the dual-panel desktop workspace.
"""

import logging
from typing import Dict, Any

try:
    from PyQt6.QtWidgets import (
        QMainWindow, QSplitter, QWidget, QHBoxLayout, QVBoxLayout, 
        QStatusBar, QTabWidget, QApplication
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
except ImportError:
    # Safe fallback if running without PyQt6 installed
    class QMainWindow: pass
    class QWidget: pass
    class QThread: pass
    class pyqtSignal:
        def __init__(self, *args, **kwargs): pass
        def connect(self, slot): pass
        def emit(self, *args, **kwargs): pass
    Qt = None

# Imports of our UI panels
from src.ui.left_panel.prompt_panel import PromptPanelWidget
from src.ui.left_panel.asset_browser import AssetBrowserWidget
from src.ui.left_panel.world_viewer import WorldViewerWidget
from src.ui.right_panel.timeline import TimelineWidget
from src.ui.right_panel.preview_player import PreviewPlayerWidget
from src.ui.right_panel.shot_viewer import ShotViewerWidget

# Imports of core pipeline components
from src.providers.gemini_provider import GeminiProvider
from src.providers.imagen_provider import ImagenProvider
from src.core.world_state.world_state import WorldStateManager
from src.core.director.director import Director
from src.core.asset_manager.asset_manager import AssetManager
from src.core.scene_composer.scene_composer import SceneComposer
from src.core.validator.validator_manager import ValidatorManager
from src.core.repair.repair_engine import RepairEngine
from src.core.orchestrator.orchestrator import PipelineOrchestrator


class PipelineWorker(QThread):
    """Asynchronous worker thread to run the AI production pipeline without freezing the UI."""
    finished = pyqtSignal()
    progress = pyqtSignal(str) # Status messages

    def __init__(self, prompt: str, director: Director, orchestrator: PipelineOrchestrator, world_state: WorldStateManager) -> None:
        super().__init__()
        self.prompt = prompt
        self.director = director
        self.orchestrator = orchestrator
        self.world_state = world_state

    def run(self) -> None:
        try:
            self.progress.emit("Orchestrator: Parsing narrative and segmenting shots...")
            plan = self.director.generate_production_plan(self.prompt)
            
            self.progress.emit(f"Orchestrator: Scheduled {len(plan.shots)} shots for asset, USD, and QC processing.")
            
            # Prepare task schedule matching plan using Director
            tasks = self.director.create_task_schedule(plan)
                
            self.orchestrator.load_task_schedule(tasks)
            
            # Run the entire pipeline execution loop
            self.orchestrator.run_pipeline()
            self.progress.emit("Orchestrator: Sequence finished successfully.")
        except Exception as e:
            self.progress.emit(f"Pipeline error: {str(e)}")
        finally:
            self.finished.emit()


class MainWindow(QMainWindow):
    """Primary window container styling 35% Control panel, 65% Timeline panel."""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__()
        self.config = config
        self.logger = logging.getLogger("MainWindow")
        
        # Instantiate backend services
        self._init_pipeline_services()
        
        # Initialize Dual-Panel UI layout
        self._init_window()

    def _init_pipeline_services(self) -> None:
        """Initializes all specialist providers and orchestrators."""
        self.ai_provider = GeminiProvider(self.config)
        self.image_provider = ImagenProvider(self.config)
        self.world_state = WorldStateManager(self.config)
        
        self.director = Director(self.ai_provider, self.world_state)
        self.asset_manager = AssetManager(self.config, self.image_provider)
        self.scene_composer = SceneComposer(self.config)
        self.validator_manager = ValidatorManager(self.ai_provider)
        self.repair_engine = RepairEngine(self.asset_manager, self.scene_composer, self.director)
        
        self.orchestrator = PipelineOrchestrator(
            self.config, self.world_state, self.asset_manager, 
            self.scene_composer, self.validator_manager, self.repair_engine
        )

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
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready.")
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create QSplitter to partition Left and Right workspace
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # --- LEFT CONTROL PANEL (35% width) ---
        self.left_container = QWidget()
        left_layout = QVBoxLayout(self.left_container)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        # Tab Widget to toggle widgets
        self.left_tabs = QTabWidget()
        self.left_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #333333;
                background-color: #202020;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #1a1a1a;
                color: #888888;
                padding: 6px 12px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border: 1px solid #333333;
                border-bottom: none;
                font-weight: bold;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background-color: #202020;
                color: #ffffff;
                border: 1px solid #333333;
                border-bottom: none;
            }
            QTabBar::tab:hover {
                background-color: #2a2a2a;
            }
        """)
        
        # Instantiate left panel widgets
        self.prompt_panel = PromptPanelWidget()
        self.asset_browser = AssetBrowserWidget()
        self.world_viewer = WorldViewerWidget()
        
        # Add to tab widget
        self.left_tabs.addTab(self.prompt_panel, "Story Prompts")
        self.left_tabs.addTab(self.asset_browser, "Asset Registry")
        self.left_tabs.addTab(self.world_viewer, "Continuity Sheet")
        
        left_layout.addWidget(self.left_tabs)
        self.splitter.addWidget(self.left_container)
        
        # --- RIGHT TIMELINE PANEL (65% width) ---
        self.right_container = QWidget()
        right_layout = QVBoxLayout(self.right_container)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(5)
        
        # Instantiate right panel widgets
        self.preview_player = PreviewPlayerWidget()
        self.timeline = TimelineWidget()
        self.shot_viewer = ShotViewerWidget()
        
        # Stack elements vertically
        right_layout.addWidget(self.preview_player, stretch=4)
        right_layout.addWidget(self.timeline, stretch=2)
        right_layout.addWidget(self.shot_viewer, stretch=3)
        
        self.splitter.addWidget(self.right_container)
        
        # Initial size splitter partitioning (e.g. 448px vs 832px)
        self.splitter.setSizes([448, 832])
        
        # Wire interactive events
        self.prompt_panel.generate_requested.connect(self.start_pipeline)
        self.timeline.shot_selected.connect(self._on_shot_selected)
        
        # Initial populate
        self._refresh_all_widgets()
        
        self.logger.info("Main Window initialized.")

    def start_pipeline(self, prompt: str) -> None:
        """Launches the background Pipeline worker to prevent UI lag."""
        self.status_bar.showMessage("Pipeline: Initiating production sequence...")
        self.prompt_panel.btn_generate.setEnabled(False)
        self.prompt_panel.btn_generate.setText("Processing Pipeline Sequence...")
        
        self.worker = PipelineWorker(prompt, self.director, self.orchestrator, self.world_state)
        self.worker.progress.connect(self.status_bar.showMessage)
        self.worker.finished.connect(self._on_pipeline_finished)
        self.worker.start()

    def _on_pipeline_finished(self) -> None:
        """Restores prompt interaction and updates all UI spreadsheets & timelines."""
        self.prompt_panel.btn_generate.setEnabled(True)
        self.prompt_panel.btn_generate.setText("Begin AI Production Pipeline")
        self.status_bar.showMessage("Pipeline: Sequence finished successfully!")
        
        # Dynamic refresh
        self._refresh_all_widgets()
        
        # Auto-select first shot
        shots = self.world_state.get_all_shots()
        if shots:
            first_shot_id = shots[0].shot_id
            self._on_shot_selected(first_shot_id)

    def _on_shot_selected(self, shot_id: str) -> None:
        """Updates inspection monitors and player previews."""
        self.preview_player.load_shot_preview(shot_id)
        self.shot_viewer.load_shot_logs(shot_id, self.world_state)

    def _refresh_all_widgets(self) -> None:
        """Re-reads state databases to keep spreadsheets, assets, and timelines updated."""
        self.asset_browser.refresh_assets(self.world_state)
        self.world_viewer.refresh_state(self.world_state)
        self.timeline.refresh_timeline(self.world_state)
