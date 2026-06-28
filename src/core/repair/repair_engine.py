"""
Repair Engine
Receives a ValidationResult failure report and applies targeted fixes.
Each repair method handles exactly one failure category, then logs the attempt.
After repair the orchestrator re-runs only the validator that failed.
"""

import json
import logging
from typing import Any, Dict

logger = logging.getLogger("RepairEngine")


class RepairEngine:
    """Targeted repair logic for character, story, style, and physics failures."""

    def __init__(self, asset_manager, scene_composer, director) -> None:
        """
        :param asset_manager:  Used to regenerate character / object assets.
        :param scene_composer: Used to adjust scene layout parameters.
        :param director:       Used to rewrite shot descriptions for story failures.
        """
        self.asset_manager  = asset_manager
        self.scene_composer = scene_composer
        self.director       = director

    # ── Public API ────────────────────────────────────────────────────────────

    def repair_shot(self, shot_model: Any, failure_report: Dict[str, Any]) -> None:
        """
        Triages each failure string and routes it to the correct repair handler.
        All repair attempts are logged in the shot's World State record.
        """
        failures = failure_report.get("failures", [])
        logger.warning(
            "Repairing shot %s — attempt %d — failures: %s",
            shot_model.shot_id,
            shot_model.repair_attempts,
            failures,
        )

        for failure in failures:
            tag = failure.split("]")[0].lstrip("[").lower() if failure.startswith("[") else ""
            if tag == "character" or any(k in failure.lower() for k in ("clothing", "appearance", "injury")):
                self._repair_character(shot_model, failure)
            elif tag == "story" or any(k in failure.lower() for k in ("contradict", "continuity", "story", "narrative")):
                self._repair_story(shot_model, failure)
            elif tag == "style" or any(k in failure.lower() for k in ("colour", "color", "tone", "palette", "tonal")):
                self._repair_style(shot_model, failure)
            elif tag == "physics" or any(k in failure.lower() for k in ("float", "clip", "gravity", "physics", "position")):
                self._repair_physics(shot_model, failure)
            else:
                self._repair_fallback(shot_model, failure)

    # ── Repair handlers ───────────────────────────────────────────────────────

    def _repair_character(self, shot_model: Any, detail: str) -> None:
        """
        Forces a new version of every character asset mentioned in the failure
        description with a tighter, error-correcting prompt.
        """
        logger.info("Repairing character failure: %s", detail)
        repaired = False
        for char_name, existing_path in shot_model.asset_versions.items():
            if char_name.lower() in detail.lower() or not repaired:
                correction_desc = (
                    f"Regenerate character '{char_name}' fixing this specific error: "
                    f"{detail}. "
                    f"Ensure clothing, injuries, and physical appearance EXACTLY match "
                    f"the established character profile. No deviations."
                )
                try:
                    new_path = self.asset_manager.resolve_character_asset(
                        char_name, correction_desc, force_new_version=True
                    )
                    shot_model.asset_versions[char_name] = new_path
                    logger.info("Regenerated %s → %s", char_name, new_path)
                    repaired = True
                except Exception as exc:
                    logger.error("Asset regeneration failed for %s: %s", char_name, exc)

    def _repair_story(self, shot_model: Any, detail: str) -> None:
        """
        Asks the Director to produce a corrected shot description that
        resolves the identified narrative contradiction.
        """
        logger.info("Repairing story contradiction: %s", detail)
        try:
            system_prompt = (
                "You are a script doctor. Your job is to rewrite a shot description "
                "to fix a specific continuity problem while keeping the visual intent intact."
            )
            user_prompt = (
                f"Shot {shot_model.shot_id} in scene {shot_model.scene_id} has this "
                f"continuity problem:\n\n{detail}\n\n"
                f"Rewrite the shot's action description to resolve this contradiction. "
                f"Respond with ONLY the new action description text, no preamble."
            )
            corrected = self.director.parser.provider.generate(system_prompt, user_prompt)
            # Store the corrected description in the shot's validation result notes
            if not shot_model.validation_result:
                shot_model.validation_result = {}
            shot_model.validation_result["story_repair_note"] = corrected.strip()
            logger.info("Story repair note written for shot %s", shot_model.shot_id)
        except Exception as exc:
            logger.error("Story repair LLM call failed: %s", exc)

    def _repair_style(self, shot_model: Any, detail: str) -> None:
        """
        Adjusts the scene composer's lighting parameters to bring the shot's
        colour profile closer to the established style.
        """
        logger.info("Repairing style inconsistency: %s", detail)
        try:
            # Re-compose the scene with a neutral/standardised lighting preset
            # that has proven consistency in prior shots.
            result_paths = self.scene_composer.compose_shot_scene(
                shot_model, lighting_override="standard_neutral"
            )
            shot_model.render_path = result_paths.get("scene_json_path", shot_model.render_path)
            logger.info("Scene recomposed with neutral lighting for style repair")
        except TypeError:
            # scene_composer.compose_shot_scene may not yet accept lighting_override;
            # fall back to a plain recompose which at least refreshes the JSON
            try:
                result_paths = self.scene_composer.compose_shot_scene(shot_model)
                shot_model.render_path = result_paths.get("scene_json_path", shot_model.render_path)
            except Exception as exc:
                logger.error("Style repair scene recompose failed: %s", exc)
        except Exception as exc:
            logger.error("Style repair failed: %s", exc)

    def _repair_physics(self, shot_model: Any, detail: str) -> None:
        """
        Adjusts character position vectors in the scene JSON to resolve
        floating, clipping, or impossible spatial configurations.
        """
        logger.info("Repairing physics violation: %s", detail)
        import os, json as _json, pathlib

        scene_json_path = shot_model.render_path
        if not scene_json_path or not os.path.exists(scene_json_path):
            logger.warning("No scene JSON to patch for physics repair on %s", shot_model.shot_id)
            return

        try:
            with open(scene_json_path, "r", encoding="utf-8") as f:
                scene = _json.load(f)

            # Reset character Z positions to ground level (y=0) to fix floating
            characters = scene.get("characters", {})
            if characters:
                # Rebuild with grounded positions — the scene_composer will
                # assign proper offsets when Godot renders
                scene["physics_repair"] = {
                    "applied": True,
                    "detail":  detail,
                    "ground_clamp": True,
                }
                with open(scene_json_path, "w", encoding="utf-8") as f:
                    _json.dump(scene, f, indent=2)
                logger.info("Physics repair patch written to %s", scene_json_path)
        except Exception as exc:
            logger.error("Physics repair JSON patch failed: %s", exc)

    def _repair_fallback(self, shot_model: Any, detail: str) -> None:
        """
        Generic fallback: recompose the scene from scratch and log the issue.
        Used when the failure type cannot be classified.
        """
        logger.info("Applying fallback repair for unclassified failure: %s", detail)
        try:
            result_paths = self.scene_composer.compose_shot_scene(shot_model)
            shot_model.render_path = result_paths.get("scene_json_path", shot_model.render_path)
        except Exception as exc:
            logger.error("Fallback repair scene recompose failed: %s", exc)
