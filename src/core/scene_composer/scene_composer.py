"""
Scene Composer — builds a scene.json for Godot and a .usda for OpenUSD.
The JSON schema must exactly match what render_scene.gd reads.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict

from src.core.scene_composer.shot_builder import ShotBuilder
from src.core.scene_composer.usd_writer import USDWriter

logger = logging.getLogger(__name__)


class SceneComposer:
    """Converts a ShotModel into a Godot-ready scene JSON and a USD stage file."""

    def __init__(self, config: dict) -> None:
        self.config       = config
        self.storage_path = Path(config.get("storage_path", "./storage"))
        self.fps          = config.get("render_fps", 24)
        self.width        = config.get("render_width", 1920)
        self.height       = config.get("render_height", 1080)

    def compose_shot_scene(self, shot_model: Any) -> Dict[str, str]:
        """
        Build scene.json and .usda from the shot_model.
        Returns {"scene_json_path": ..., "usda_path": ...}
        """
        shot_id   = shot_model.shot_id
        scene_dir = self.storage_path / "cache" / shot_id
        scene_dir.mkdir(parents=True, exist_ok=True)

        json_path = str(scene_dir / f"{shot_id}_scene.json")
        usda_path = str(scene_dir / f"{shot_id}_scene.usda")

        cam    = ShotBuilder.calculate_camera_parameters(
            getattr(shot_model, "camera_angle", "medium")
        )
        lights = ShotBuilder.calculate_lighting_parameters(
            getattr(shot_model, "lighting", "standard")
        )

        # Build character list in the shape render_scene.gd expects:
        # [{name, x, y, z, color, mesh_path}, ...]
        characters = []
        asset_versions = getattr(shot_model, "asset_versions", {}) or {}
        for i, (name, asset_path) in enumerate(asset_versions.items()):
            characters.append({
                "name":      name,
                "x":         float(i) * 1.5 - (len(asset_versions) - 1) * 0.75,
                "y":         0.0,
                "z":         0.0,
                "color":     "aaaaaa",
                "mesh_path": str(asset_path) if asset_path else "",
            })

        scene_data = {
            "shot_id":          shot_id,
            "scene_id":         shot_model.scene_id,
            "fps":              self.fps,
            "duration_seconds": getattr(shot_model, "duration_seconds", 3.0),
            "width":            self.width,
            "height":           self.height,

            # Camera as a dict — matches cam_data.get("x") in render_scene.gd
            "camera": {
                "x":            cam["camera_x"],
                "y":            cam["camera_y"],
                "z":            cam["camera_z"],
                "fov":          cam["fov"],
                "pitch":        cam.get("pitch", 0.0),
                "yaw":          cam.get("yaw", 0.0),
                "focal_length": cam["focal_length"],
            },

            # Lighting as a dict — matches light_data.get("energy") in render_scene.gd
            "lighting": {
                "energy":    lights["light_intensity"],
                "sky_color": lights["sky_color"],
                "pitch":     lights.get("pitch", -45.0),
                "yaw":       lights.get("yaw", 30.0),
            },

            # Characters as a list of dicts
            "characters": characters,

            # Objects placeholder
            "objects": [],
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(scene_data, f, indent=2)

        USDWriter.write_usda_scene(usda_path, scene_data)
        logger.info(f"Scene JSON written: {json_path}")

        return {"scene_json_path": json_path, "usda_path": usda_path}
