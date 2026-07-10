"""
Task Runner — executes individual pipeline tasks:
asset_resolution, scene_composition, scene_rendering, shot_validation.
"""
import logging
import os
from pathlib import Path
from typing import Dict, Any


class TaskRunner:
    """Routes task dicts to the correct sub-system handler."""

    def __init__(self, asset_manager, scene_composer, process_manager,
                 validator_manager, world_state, config: dict) -> None:
        self.asset_manager     = asset_manager
        self.scene_composer    = scene_composer
        self.process_manager   = process_manager
        self.validator_manager = validator_manager
        self.world_state       = world_state
        self.storage_path      = Path(config.get("storage_path", "./storage"))
        self.godot_path        = config.get("godot_path", "")   # read from config, not task
        self.logger            = logging.getLogger("TaskRunner")

    def execute_task(self, task: Dict[str, Any], shot_model: Any) -> Dict[str, Any]:
        t = task["type"]
        self.logger.info(f"Task {task.get('task_id')} ({t}) for {task['shot_id']}")
        if t == "asset_resolution":  return self._run_asset_resolution(task, shot_model)
        if t == "scene_composition": return self._run_scene_composition(task, shot_model)
        if t == "scene_rendering":   return self._run_scene_rendering(task, shot_model)
        if t == "shot_validation":   return self._run_shot_validation(task, shot_model)
        raise ValueError(f"Unknown task type: {t}")

    def _run_asset_resolution(self, task: Dict[str, Any], shot_model: Any) -> Dict[str, Any]:
        from src.core.world_state.character_db import CharacterModel
        from src.core.world_state.object_db import ObjectModel
        from src.core.world_state.world_db import WorldEventModel

        data       = task.get("data", {})
        characters = data.get("characters", [])
        objects    = data.get("objects", [])
        lighting   = data.get("lighting", "Standard")
        resolved   = {}

        for name in characters:
            path = self.asset_manager.resolve_character_asset(name, f"Character named {name}")
            resolved[name] = path
            rec = self.world_state.get_character(name)
            if not rec:
                self.world_state.save_character(CharacterModel(
                    name=name,
                    appearance={"description": f"Visual identity of {name}"},
                    clothing={"style": "Standard"}, injuries={},
                    history=f"First appeared in {shot_model.shot_id}",
                    last_seen_shot_id=shot_model.shot_id
                ))
            else:
                rec.last_seen_shot_id = shot_model.shot_id
                self.world_state.save_character(rec)

        for name in objects:
            path = self.asset_manager.resolve_object_asset(name, f"Prop named {name}")
            resolved[name] = path
            rec = self.world_state.get_object(name)
            if not rec:
                self.world_state.save_object(ObjectModel(
                    name=name, condition="Intact",
                    location=f"Shot {shot_model.shot_id}", owner="None", version=1,
                    history=f"Registered in {shot_model.shot_id}"
                ))
            else:
                rec.location = f"Shot {shot_model.shot_id}"
                self.world_state.save_object(rec)

        if not self.world_state.get_world_event(shot_model.shot_id):
            ll = lighting.lower()
            self.world_state.save_world_event(WorldEventModel(
                shot_id=shot_model.shot_id,
                time_of_day="Night" if "low-key" in ll or "dark" in ll else "Day",
                weather="Rainy" if "rain" in ll else "Clear",
                lighting=lighting, damage_state={},
                events={"description": f"Settings for {shot_model.shot_id}"}
            ))

        shot_model.asset_versions = resolved
        return {"status": "success", "resolved_assets": resolved}

    def _run_scene_composition(self, task: Dict[str, Any], shot_model: Any) -> Dict[str, Any]:
        # Copy shot metadata onto model so scene_composer can use it
        data = task.get("data", {})
        if not hasattr(shot_model, "camera_angle") or not shot_model.camera_angle:
            shot_model.camera_angle = data.get("camera_angle", "medium")
        if not hasattr(shot_model, "duration_seconds") or not shot_model.duration_seconds:
            shot_model.duration_seconds = data.get("duration_seconds", 3.0)

        result = self.scene_composer.compose_shot_scene(shot_model)
        shot_model.render_path = result.get("scene_json_path", "")
        return {"status": "success", "composer_paths": result}

    def _run_scene_rendering(self, task: Dict[str, Any], shot_model: Any) -> Dict[str, Any]:
        """
        Produce frames for this shot.
        - If Godot is configured and the binary exists: runs real headless render.
        - Otherwise: generates one AI image placeholder so the pipeline and UI
          always have something to show regardless of Godot installation.
        """
        if not shot_model.render_path:
            raise FileNotFoundError(f"No scene JSON for shot {shot_model.shot_id}")

        output_dir = self.storage_path / "cache" / shot_model.shot_id
        output_dir.mkdir(parents=True, exist_ok=True)
        frame_file = output_dir / "frame_0000.png"

        # Always generate a placeholder first so validation has something to check
        if not frame_file.exists():
            description = getattr(shot_model, "description", shot_model.shot_id)
            prompt    = f"Cinematic film frame. {description}"
            img_bytes = self.asset_manager.image_provider.generate(prompt)
            frame_file.write_bytes(img_bytes)
            self.logger.info(f"Placeholder frame written: {frame_file}")

        # Attempt real Godot render on top if binary is available
        godot_bin = self.godot_path
        if godot_bin and os.path.isfile(godot_bin):
            try:
                # Load the scene JSON we built in scene_composition
                import json as _json
                with open(shot_model.render_path) as f:
                    scene_data = _json.load(f)

                from src.integrations.godot.godot_bridge import GodotBridge
                bridge = GodotBridge(self.process_manager, {"godot_path": godot_bin})
                frames = bridge.render_shot(shot_model.shot_id, scene_data, str(output_dir))
                if frames:
                    self.logger.info(f"Godot rendered {len(frames)} real frames for {shot_model.shot_id}")
                else:
                    self.logger.warning(f"Godot returned no frames for {shot_model.shot_id} — keeping placeholder")
            except Exception as e:
                self.logger.error(f"Godot render error for {shot_model.shot_id}: {e} — keeping placeholder")
        else:
            if godot_bin:
                self.logger.warning(f"Godot binary not found at {godot_bin!r} — using placeholder.")
            else:
                self.logger.info("godot_path not set in config — using placeholder frame.")

        shot_model.render_path = str(output_dir)
        return {"status": "success", "output_directory": str(output_dir)}

    def _run_shot_validation(self, task: Dict[str, Any], shot_model: Any) -> Dict[str, Any]:
        report = self.validator_manager.run_all_validators(shot_model, self.world_state)
        shot_model.validation_result = report
        return {"status": "success" if report["passed"] else "failed", "report": report}
