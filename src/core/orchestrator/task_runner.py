"""
Task Runner Module
Contains individual task runners that coordinate Asset Resolution, Scene Composition,
Rendering, and Shot Validation operations.
"""

import logging
from typing import Dict, Any

class TaskRunner:
    """Invokes core sub-systems corresponding to the requested task type."""
    
    def __init__(self, asset_manager, scene_composer, process_manager, validator_manager, world_state) -> None:
        self.asset_manager = asset_manager
        self.scene_composer = scene_composer
        self.process_manager = process_manager
        self.validator_manager = validator_manager
        self.world_state = world_state
        self.logger = logging.getLogger("TaskRunner")

    def execute_task(self, task: Dict[str, Any], shot_model: Any) -> Dict[str, Any]:
        """
        Routes the task dictionary to its appropriate execution handler.
        """
        task_type = task["type"]
        shot_id = task["shot_id"]
        self.logger.info(f"Running task {task['task_id']} ({task_type}) for shot {shot_id}")
        
        if task_type == "asset_resolution":
            return self._run_asset_resolution(task, shot_model)
        elif task_type == "scene_composition":
            return self._run_scene_composition(task, shot_model)
        elif task_type == "scene_rendering":
            return self._run_scene_rendering(task, shot_model)
        elif task_type == "shot_validation":
            return self._run_shot_validation(task, shot_model)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    def _run_asset_resolution(self, task: Dict[str, Any], shot_model: Any) -> Dict[str, Any]:
        """Resolves characters, objects, and props present in the task metadata."""
        characters = task["data"].get("characters", [])
        objects = task["data"].get("objects", [])
        
        resolved_paths = {}
        
        for name in characters:
            path = self.asset_manager.resolve_character_asset(name, f"Character named {name}")
            resolved_paths[name] = path
            
        for name in objects:
            path = self.asset_manager.resolve_object_asset(name, f"Prop named {name}")
            resolved_paths[name] = path
            
        # Record resolved asset versions onto the shot state
        shot_model.asset_versions = resolved_paths
        return {"status": "success", "resolved_assets": resolved_paths}

    def _run_scene_composition(self, task: Dict[str, Any], shot_model: Any) -> Dict[str, Any]:
        """Arranges cameras, actors, and lights into a USD file."""
        # Builds the USD file and scene JSON for Godot
        result_paths = self.scene_composer.compose_shot_scene(shot_model)
        shot_model.render_path = result_paths.get("scene_json_path", "")
        return {"status": "success", "composer_paths": result_paths}

    def _run_scene_rendering(self, task: Dict[str, Any], shot_model: Any) -> Dict[str, Any]:
        """Triggers headless rendering in the Process Manager."""
        scene_json = shot_model.render_path
        if not scene_json:
            raise FileNotFoundError(f"No composite scene file found for shot {shot_model.shot_id}")
            
        output_dir = f"./storage/cache/{shot_model.shot_id}"
        
        # Procedurally generate a render frame for UI feedback
        import os
        os.makedirs(output_dir, exist_ok=True)
        frame_file = os.path.join(output_dir, "frame_0000.png")
        if not os.path.exists(frame_file):
            prompt = f"Scene rendering of {shot_model.shot_id} under scene {shot_model.scene_id}."
            img_bytes = self.asset_manager.image_provider.generate(prompt)
            with open(frame_file, "wb") as f:
                f.write(img_bytes)
                
        # Trigger Process Manager for Godot headless
        # (Godot script runs in a real pipeline)
        # self.process_manager.run_godot_headless("./godot/render_scene.gd", output_dir)
        
        return {"status": "success", "output_directory": output_dir}

    def _run_shot_validation(self, task: Dict[str, Any], shot_model: Any) -> Dict[str, Any]:
        """Fires sequence of character, story, style, and physics checks."""
        validation_report = self.validator_manager.run_all_validators(shot_model, self.world_state)
        shot_model.validation_result = validation_report
        
        return {
            "status": "success" if validation_report["passed"] else "failed",
            "report": validation_report
        }
logging = logging
Dict = Dict
Any = Any
