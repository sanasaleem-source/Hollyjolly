"""
Repair Engine — targeted fixes for validation failures.
Each handler fixes exactly one failure type.
Uses centralised prompts from src/providers/prompts.py.
"""
import json
import logging
import os
from typing import Any, Dict
from src.providers.prompts import (
    REPAIR_STORY_SYSTEM, REPAIR_STORY_USER,
    REPAIR_CHARACTER_SYSTEM, REPAIR_CHARACTER_USER
)

logger = logging.getLogger(__name__)


class RepairEngine:
    """Targeted repair logic for character, story, style, and physics failures."""

    def __init__(self, asset_manager, scene_composer, director, world_state=None) -> None:
        self.asset_manager  = asset_manager
        self.scene_composer = scene_composer
        self.director       = director
        self.world_state    = world_state  # injected after build_pipeline

    def repair_shot(self, shot_model: Any, failure_report: Dict[str, Any]) -> None:
        """Triage failures and route each to the correct repair handler."""
        failures = failure_report.get("failures", [])
        logger.warning(
            "Repairing shot %s — attempt %d — %d failure(s)",
            shot_model.shot_id, shot_model.repair_attempts, len(failures)
        )
        for failure in failures:
            tag = failure.split("]")[0].lstrip("[").lower() if failure.startswith("[") else ""
            if tag == "character" or any(k in failure.lower() for k in ("clothing", "appearance", "injury")):
                self._repair_character(shot_model, failure)
            elif tag == "story" or any(k in failure.lower() for k in ("contradict", "continuity", "narrative")):
                self._repair_story(shot_model, failure)
            elif tag == "style" or any(k in failure.lower() for k in ("colour", "color", "tone", "palette")):
                self._repair_style(shot_model, failure)
            elif tag == "physics" or any(k in failure.lower() for k in ("float", "clip", "gravity", "physics")):
                self._repair_physics(shot_model, failure)
            else:
                self._repair_fallback(shot_model, failure)

    def _repair_character(self, shot_model: Any, detail: str) -> None:
        logger.info("Repairing character failure: %s", detail)
        for char_name in list(shot_model.asset_versions.keys()):
            if char_name.lower() not in detail.lower():
                continue
            char      = self.world_state.get_character(char_name) if self.world_state else None
            char_desc = json.dumps(char.model_dump()) if char else f"Character named {char_name}"
            system    = REPAIR_CHARACTER_SYSTEM
            user      = REPAIR_CHARACTER_USER.format(
                character_name=char_name,
                character_description=char_desc,
                failure_detail=detail
            )
            try:
                corrected_prompt = self.director.parser.provider.generate(system, user)
                new_path = self.asset_manager.resolve_character_asset(
                    char_name, corrected_prompt.strip(), force_new_version=True
                )
                shot_model.asset_versions[char_name] = new_path
                logger.info("Regenerated %s → %s", char_name, new_path)
            except Exception as e:
                logger.error("Character repair failed for %s: %s", char_name, e)

    def _repair_story(self, shot_model: Any, detail: str) -> None:
        logger.info("Repairing story contradiction: %s", detail)
        if not self.director:
            return
        system = REPAIR_STORY_SYSTEM
        user   = REPAIR_STORY_USER.format(
            shot_id=shot_model.shot_id,
            scene_id=shot_model.scene_id,
            failure_detail=detail
        )
        try:
            corrected = self.director.parser.provider.generate(system, user)
            if not shot_model.validation_result:
                shot_model.validation_result = {}
            shot_model.validation_result["story_repair_note"] = corrected.strip()
        except Exception as e:
            logger.error("Story repair failed: %s", e)

    def _repair_style(self, shot_model: Any, detail: str) -> None:
        logger.info("Repairing style failure: %s", detail)
        try:
            result = self.scene_composer.compose_shot_scene(shot_model)
            shot_model.render_path = result.get("scene_json_path", shot_model.render_path)
        except Exception as e:
            logger.error("Style repair recompose failed: %s", e)

    def _repair_physics(self, shot_model: Any, detail: str) -> None:
        logger.info("Repairing physics violation: %s", detail)
        scene_path = shot_model.render_path
        if not scene_path or not os.path.exists(scene_path):
            logger.warning("No scene JSON for physics repair on %s", shot_model.shot_id)
            return
        try:
            with open(scene_path, "r", encoding="utf-8") as f:
                scene = json.load(f)
            scene["physics_repair"] = {"applied": True, "detail": detail, "ground_clamp": True}
            with open(scene_path, "w", encoding="utf-8") as f:
                json.dump(scene, f, indent=2)
        except Exception as e:
            logger.error("Physics repair failed: %s", e)

    def _repair_fallback(self, shot_model: Any, detail: str) -> None:
        logger.info("Fallback repair for: %s", detail)
        try:
            result = self.scene_composer.compose_shot_scene(shot_model)
            shot_model.render_path = result.get("scene_json_path", shot_model.render_path)
        except Exception as e:
            logger.error("Fallback repair failed: %s", e)
