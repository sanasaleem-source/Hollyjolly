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
        self.asset_manager    = asset_manager
        self.scene_composer   = scene_composer
        self.process_manager  = process_manager
        self.validator_manager = validator_manager
        self.world_state      = world_state
        self.storage_path     = Path(config.get("storage_path", "./storage"))
        self.logger           = logging.getLogger("TaskRunner")

    def execute_task(self, task: Dict[str, Any], shot_model: Any) -> Dict[str, Any]:
        t = task["type"]
        self.logger.info(f"Task {task.get('task_id')} ({t}) for {task['shot_id']}")
        if t == "asset_resolution":   return self._run_asset_resolution(task, shot_model)
        if t == "scene_composition":  return self._run_scene_composition(task, shot_model)
        if t == "scene_rendering":    return self._run_scene_rendering(task, shot_model)
        if t == "shot_validation":    return self._run_shot_validation(task, shot_model)
        raise ValueError(f"Unknown task type: {t}")

    def _run_asset_resolution(self, task: Dict[str, Any], shot_model: Any) -> Dict[str, Any]:
        from src.core.world_state.character_db import CharacterModel
        from src.core.world_state.object_db import ObjectModel
        from src.core.world_state.world_db import WorldEventModel

        data       = task.get("data", {})
        characters = data.get("characters", [])
        objects    = data.get("objects",    [])
        lighting   = data.get("lighting",   "Standard")
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
        result = self.scene_composer.compose_shot_scene(shot_model)
        shot_model.render_path = result.get("scene_json_path", "")
        return {"status": "success", "composer_paths": result}

    def _run_scene_rendering(self, task: Dict[str, Any], shot_model: Any) -> Dict[str, Any]:
        """
        Produce at least one frame so the pipeline and UI have something to show.
        Phase 1 generates a placeholder image from the AI image provider.
        Godot headless rendering is invoked when godot_path is configured and valid.
        """
        if not shot_model.render_path:
            raise FileNotFoundError(f"No scene file for shot {shot_model.shot_id}")

        # Use config-driven storage path — never hardcoded
        output_dir = self.storage_path / "cache" / shot_model.shot_id
        output_dir.mkdir(parents=True, exist_ok=True)
        frame_file = output_dir / "frame_0000.png"

        if not frame_file.exists():
            prompt    = f"Cinematic film frame: {shot_model.shot_id} in scene {shot_model.scene_id}."
            img_bytes = self.asset_manager.image_provider.generate(prompt)
            frame_file.write_bytes(img_bytes)

        # Attempt real Godot headless render — log warning if Godot not found
        godot_path = task.get("godot_path") or ""
        if godot_path and os.path.isfile(godot_path):
            from src.integrations.godot.godot_bridge import GodotBridge
            bridge = GodotBridge(self.process_manager, {"godot_path": godot_path})
            frames = bridge.render_shot(shot_model.shot_id, {}, str(output_dir))
            if frames:
                self.logger.info(f"Godot rendered {len(frames)} frames for {shot_model.shot_id}")
        else:
            self.logger.info(
                f"Godot not found at {godot_path!r} — using placeholder frame. "
                "Set godot_path in config.yaml to enable real rendering."
            )

        shot_model.render_path = str(output_dir)
        return {"status": "success", "output_directory": str(output_dir)}

    def _run_shot_validation(self, task: Dict[str, Any], shot_model: Any) -> Dict[str, Any]:
        report = self.validator_manager.run_all_validators(shot_model, self.world_state)
        shot_model.validation_result = report
        return {"status": "success" if report["passed"] else "failed", "report": report}
