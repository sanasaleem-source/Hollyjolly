"""
Godot Bridge — spawns Godot 4 headless, passes scene JSON, collects rendered frames.
"""
import json
import logging
import tempfile
from pathlib import Path
from typing import Optional
from src.integrations.godot.frame_collector import FrameCollector

logger = logging.getLogger(__name__)


class GodotBridge:
    """Manages headless Godot rendering sessions."""

    def __init__(self, process_manager, config: dict) -> None:
        self.pm = process_manager
        self.godot_path = config.get("godot_path", "godot")
        self.script_path = Path(__file__).parent / "render_scene.gd"
        self.collector = FrameCollector()

    def render_shot(self, shot_id: str, scene_data: dict, output_dir: str) -> list[str]:
        """
        Write scene JSON, spawn Godot headless, collect and return frame paths.
        Returns list of rendered frame file paths, or empty list on failure.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Write scene JSON to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(scene_data, f, indent=2)
            scene_json_path = f.name

        logger.info(f"Rendering shot {shot_id} → {output_dir}")

        cmd = [
            self.godot_path,
            "--headless",
            "--script", str(self.script_path),
            "--", scene_json_path, str(output_path)
        ]

        result = self.pm.run_process(cmd, timeout_sec=300)

        if result.returncode != 0:
            logger.error(f"Godot render failed for shot {shot_id}:\n{result.stderr}")
            return []

        frames = self.collector.collect(str(output_path))
        logger.info(f"Shot {shot_id} rendered {len(frames)} frames")
        return frames
