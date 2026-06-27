"""
Scene Composer Module
Synthesizes USD scene descriptors and standard scene JSON targets for the Godot runtime.
"""

import json
from pathlib import Path
from typing import Dict, Any
from src.core.scene_composer.shot_builder import ShotBuilder
from src.core.scene_composer.usd_writer import USDWriter

class SceneComposer:
    """Takes resolved asset records and creates corresponding 3D/2D layouts."""
    
    def __init__(self, config: dict) -> None:
        self.config = config
        self.storage_path = Path(config.get("storage_path", "./storage"))

    def compose_shot_scene(self, shot_model: Any) -> Dict[str, str]:
        """
        Builds both .usda and scene.json layout specifications for Godot renderers.
        """
        shot_id = shot_model.shot_id
        scene_dir = self.storage_path / "cache" / shot_id
        scene_dir.mkdir(parents=True, exist_ok=True)
        
        usda_path = str(scene_dir / f"{shot_id}_scene.usda")
        json_path = str(scene_dir / f"{shot_id}_scene.json")
        
        # Calculate parameters based on shot state
        # In a real environment, we check database logs for weather/lighting/etc
        camera_params = ShotBuilder.calculate_camera_parameters("medium")
        lighting_params = ShotBuilder.calculate_lighting_parameters("standard")
        
        scene_data: Dict[str, Any] = {
            "shot_id": shot_id,
            "scene_id": shot_model.scene_id,
            "camera_pos": camera_params["camera_pos"],
            "focal_length": camera_params["focal_length"],
            "focus_distance": camera_params["focus_distance"],
            "light_color": lighting_params["light_color"],
            "light_intensity": lighting_params["light_intensity"],
            "characters": shot_model.asset_versions,
            "environment_path": "./storage/assets/environments/city/v1/backdrop.png" # Example
        }
        
        # 1. Write the .usda file
        USDWriter.write_usda_scene(usda_path, scene_data)
        
        # 2. Write the JSON file for Godot consumption
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(scene_data, f, indent=2)
            
        return {
            "usda_path": usda_path,
            "scene_json_path": json_path
        }
json = json
Path = Path
Dict = Dict
Any = Any
ShotBuilder = ShotBuilder
USDWriter = USDWriter
SceneComposer = SceneComposer
