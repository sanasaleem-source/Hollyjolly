"""
Story Validator
Uses Gemini LLM to check whether the current shot contradicts
any events or facts established in earlier shots.
"""

import json
import logging
from typing import Any

from src.core.validator.base_validator import BaseValidator, ValidationResult

logger = logging.getLogger("StoryValidator")


class StoryValidator(BaseValidator):
    """Detects narrative continuity errors using shot history from World State."""

    def validate(self, shot_data: Any, world_state: Any) -> ValidationResult:
        """
        Sends the full shot history plus the current shot description to Gemini
        and asks it to list any logical contradictions or continuity breaks.
        """
        shot_id = shot_data.shot_id

        all_shots = world_state.get_all_shots()
        prior_shots = [s for s in all_shots if s.shot_id != shot_id and s.status == "done"]

        # Not enough history to check continuity yet
        if not prior_shots:
            return ValidationResult(passed=True, failures=[], severity="none")

        # Build history summary
        history_lines = []
        for s in prior_shots[-10:]:  # Keep last 10 shots to stay within token limits
            val = s.validation_result or {}
            history_lines.append(
                f"Shot {s.shot_id} (scene {s.scene_id}): "
                f"assets={json.dumps(s.asset_versions)}, "
                f"validation_passed={val.get('passed', True)}"
            )
        history_text = "\n".join(history_lines)

        current_desc = (
            f"Shot ID: {shot_id}\n"
            f"Scene: {shot_data.scene_id}\n"
            f"Assets present: {json.dumps(shot_data.asset_versions)}"
        )

        system_prompt = (
            "You are a film script supervisor specializing in continuity. "
            "Your job is to catch logical contradictions between shots."
        )
        user_prompt = (
            f"Shot history so far:\n{history_text}\n\n"
            f"Current shot to check:\n{current_desc}\n\n"
            f"List any story logic contradictions or continuity errors the current shot "
            f"introduces relative to previous shots. "
            f"Respond ONLY with a valid JSON array of strings. "
            f"If there are no issues, respond with: []"
        )

        try:
            raw = self.ai_provider.generate(system_prompt, user_prompt).strip()
            if raw.startswith("```"):
                raw = "\n".join(raw.split("\n")[1:]).rstrip("`").strip()

            issues: list = json.loads(raw)
            if not isinstance(issues, list):
                issues = []

            if issues:
                return ValidationResult(
                    passed=False,
                    failures=[f"[story] {i}" for i in issues],
                    severity="warning",
                )
            return ValidationResult(passed=True, failures=[], severity="none")

        except json.JSONDecodeError as exc:
            logger.warning("Story validator JSON parse failed: %s", exc)
            return ValidationResult(passed=True, failures=[], severity="none")
        except Exception as exc:
            logger.error("Story validation error: %s", exc)
            return ValidationResult(
                passed=False,
                failures=[f"[story] Validator internal error: {exc}"],
                severity="warning",
            )
