"""
AI Production Studio — Entry Point.
Loads config, shows API key setup on first run, initialises all systems, launches PyQt6 UI.
"""
import sys
import logging
import yaml
from pathlib import Path
from PyQt6.QtWidgets import QApplication

LOG_PATH = Path("storage/logs")
LOG_PATH.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH / "studio.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    config_path = Path("config.yaml")
    if not config_path.exists():
        logger.warning("config.yaml not found — run setup.py first")
        return {}
    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def ensure_storage(config: dict) -> None:
    base = Path(config.get("storage_path", "./storage"))
    for folder in ["database", "projects", "assets/characters",
                   "assets/objects", "assets/environments", "cache", "logs"]:
        (base / folder).mkdir(parents=True, exist_ok=True)


def needs_api_key(config: dict) -> bool:
    key = config.get("gemini_api_key", "")
    return not key or key == "GEMINI_API_KEY_HERE"


def show_api_key_dialog(config: dict) -> dict:
    """Show API key setup dialog before main window if key is missing."""
    from src.ui.api_key_dialog import APIKeyDialog
    app_ref = QApplication.instance()
    dialog = APIKeyDialog(config)
    if dialog.exec():
        config = dialog.get_updated_config()
        # Persist to config.yaml
        with open("config.yaml", "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        logger.info("API key saved to config.yaml")
    return config


def build_pipeline(config: dict):
    """Instantiate and wire all pipeline components. Accepts config dict."""
    from src.core.world_state.world_state import WorldStateManager
    from src.providers.gemini_provider import GeminiProvider
    from src.providers.imagen_provider import ImagenProvider
    from src.core.asset_manager.asset_manager import AssetManager
    from src.core.scene_composer.scene_composer import SceneComposer
    from src.core.validator.validator_manager import ValidatorManager
    from src.core.repair.repair_engine import RepairEngine
    from src.core.director.director import Director
    from src.core.orchestrator.orchestrator import PipelineOrchestrator

    # All components receive config dict — no db_path string anywhere
    world_state    = WorldStateManager(config)
    llm_provider   = GeminiProvider(config)
    image_provider = ImagenProvider(config)
    asset_manager  = AssetManager(config, image_provider)
    scene_composer = SceneComposer(config)
    validator_mgr  = ValidatorManager(llm_provider, llm_provider)
    repair_engine  = RepairEngine(asset_manager, scene_composer, None)
    director       = Director(llm_provider, world_state)
    repair_engine.director = director

    orchestrator = PipelineOrchestrator(
        config, world_state, asset_manager,
        scene_composer, validator_mgr, repair_engine
    )
    return director, orchestrator, world_state, asset_manager


def main() -> None:
    logger.info("AI Production Studio starting...")
    config = load_config()
    ensure_storage(config)

    app = QApplication(sys.argv)
    app.setApplicationName("AI Production Studio")
    app.setStyle("Fusion")

    # Show API key dialog if not configured
    if needs_api_key(config):
        config = show_api_key_dialog(config)

    from src.ui.main_window import MainWindow

    try:
        director, orchestrator, world_state, asset_manager = build_pipeline(config)
    except Exception as e:
        logger.error(f"Pipeline init failed: {e} — launching UI in limited mode")
        director = orchestrator = world_state = asset_manager = None

    window = MainWindow(config, world_state, orchestrator)

    if orchestrator and director:
        def run_pipeline(prompt: str, target: str) -> None:
            from PyQt6.QtCore import QThread, QObject, pyqtSignal

            class Worker(QObject):
                shot_updated  = pyqtSignal(str, str, str)
                pipeline_done = pyqtSignal(str)
                pipeline_error = pyqtSignal(str)

                def __init__(self, prompt, target):
                    super().__init__()
                    self.prompt = prompt
                    self.target = target

                def run(self):
                    try:
                        from src.core.director.task_planner import TaskPlanner
                        plan = director.generate_production_plan(self.prompt)
                        tasks = director.create_task_schedule(plan)
                        orchestrator.load_task_schedule(tasks)

                        shot_ids = [s.shot_id for s in plan.shots]
                        window.timeline.load_shots(shot_ids)

                        def on_update(sid, status, fp=""):
                            self.shot_updated.emit(sid, status, fp)

                        orchestrator.run_pipeline()
                        self.pipeline_done.emit("")
                    except Exception as ex:
                        logger.error(f"Pipeline error: {ex}", exc_info=True)
                        self.pipeline_error.emit(str(ex))

            thread = QThread()
            worker = Worker(prompt, target)
            worker.moveToThread(thread)
            worker.shot_updated.connect(window.update_shot_status)
            worker.pipeline_done.connect(window.pipeline_complete)
            worker.pipeline_error.connect(
                lambda msg: window.status.showMessage(f"Error: {msg}")
            )
            thread.started.connect(worker.run)
            thread.start()
            window._thread = thread
            window._worker = worker

        window.pipeline_requested.connect(run_pipeline)

    window.show()
    logger.info("UI launched")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
