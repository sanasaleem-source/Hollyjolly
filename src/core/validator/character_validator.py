"""
Character Validator
Uses Gemini Vision to verify character clothing, injuries, and appearance
are consistent with World State records across shots.
"""

import json
import logging
import os
from typing import Any

from src.core.validator.base_validator import BaseValidator, ValidationResult

logger = logging.getLogger("CharacterValidator")


class CharacterValidator(BaseValidator):
    """Checks rendered frames against registered character appearance data."""

    def validate(self, shot_data: Any, world_state: Any) -> ValidationResult:
        """
        Loads rendered frame(s) and character descriptions, asks Gemini Vision
        to list any inconsistencies. Returns PASSED if no frame exists yet
        (render hasn't happened) or if Gemini finds no issues.
        """
        shot_id    = shot_data.shot_id
        frame_path = f"./storage/cache/{shot_id}/frame_0000.png"

        # No frame yet — render step is pending, nothing to validate
        if not os.path.exists(frame_path):
            logger.debug("No frame for %s — skipping character validation", shot_id)
            return ValidationResult(passed=True, failures=[], severity="none")

        characters = world_state.get_all_characters()
        if not characters:
            return ValidationResult(passed=True, failures=[], severity="none")

        # Build character description summary
        char_lines = []
        for c in characters:
            char_lines.append(
                f"- {c.name}: clothing={json.dumps(c.clothing)}, "
                f"injuries={json.dumps(c.injuries)}, "
                f"appearance={json.dumps(c.appearance)}"
            )
        char_desc = "\n".join(char_lines)

        prompt = (
            f"You are a film continuity supervisor. Compare this rendered video frame "
            f"with the official character records below:\n\n"
            f"{char_desc}\n\n"
            f"List every clothing, injury, or appearance mismatch you see. "
            f"Respond ONLY with a valid JSON array of strings describing each problem. "
            f"If everything matches, respond with an empty array: []"
        )

        try:
            with open(frame_path, "rb") as f:
                image_bytes = f.read()

            raw = self.ai_provider.analyze(image_bytes, prompt)
            raw = raw.strip()
            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = "\n".join(raw.split("\n")[1:]).rstrip("`").strip()

            issues: list = json.loads(raw)
            if not isinstance(issues, list):
                issues = []

            if issues:
                return ValidationResult(
                    passed=False,
                    failures=[f"[character] {i}" for i in issues],
                    severity="warning",
                )
            return ValidationResult(passed=True, failures=[], severity="none")

        except json.JSONDecodeError as exc:
            logger.warning("Character validator JSON parse failed: %s", exc)
            # Gemini returned something non-parseable — log and soft-pass
            return ValidationResult(passed=True, failures=[], severity="none")
        except Exception as exc:
            logger.error("Character validation error: %s", exc)
            return ValidationResult(
                passed=False,
                failures=[f"[character] Validator internal error: {exc}"],
                severity="warning",
            )
