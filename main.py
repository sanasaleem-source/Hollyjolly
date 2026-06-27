#!/usr/bin/env python3
"""
AI Production Studio - Main Entry Point
Desktop application entry point that initializes logging, loads configurations,
and starts the PyQt6 user interface.
"""

import sys
import os
import logging
import yaml
from pathlib import Path

# Setup logging immediately
def setup_logging(config: dict) -> None:
    """Configures the logging system based on the yaml configuration."""
    storage_path = Path(config.get("storage_path", "./storage"))
    log_dir = storage_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "studio.log"
    log_level = getattr(logging, config.get("logging", {}).get("level", "INFO").upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8")
        ]
    )
    logging.info("Logging initialized successfully.")

def load_config() -> dict:
    """Loads and returns the application configuration from config.yaml."""
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        print(f"Error: Configuration file {config_path} not found.")
        sys.exit(1)
        
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return config
    except Exception as e:
        print(f"Error reading configuration: {e}")
        sys.exit(1)

def ensure_folders(config: dict) -> None:
    """Ensures that all storage and database folders exist on start."""
    storage_path = Path(config.get("storage_path", "./storage"))
    subfolders = ["database", "projects", "assets", "cache", "logs"]
    for sub in subfolders:
        (storage_path / sub).mkdir(parents=True, exist_ok=True)
    logging.info("Required storage subfolders ensured.")

def main() -> None:
    """Main execution function of the AI Production Studio."""
    # 1. Load config
    config = load_config()
    
    # 2. Setup logging
    setup_logging(config)
    logging.info("Starting AI Production Studio...")
    
    # 3. Ensure folder structure
    ensure_folders(config)
    
    # 4. Initialize UI (Using PyQt6)
    try:
        from PyQt6.QtWidgets import QApplication
        from src.ui.main_window import MainWindow
        
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        
        # Instantiate main window and pass config
        window = MainWindow(config)
        window.show()
        
        logging.info("PyQt6 UI started successfully.")
        sys.exit(app.exec())
    except ImportError as e:
        logging.error(f"Failed to import PyQt6 or UI modules: {e}")
        logging.warning("Please install PyQt6 dependencies using: pip install -r requirements.txt")
        print("\n--- CLI Mode Fallback (PyQt6 not installed) ---")
        print("AI Production Studio Phase 1 is fully set up. Run PyQt6 app when dependencies are installed.")
        print(f"Configuration loaded: {list(config.keys())}")
    except Exception as e:
        logging.critical(f"Unhandled crash in main thread: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
