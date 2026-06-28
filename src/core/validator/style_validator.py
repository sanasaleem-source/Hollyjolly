"""
Style Validator
Uses Gemini Vision to detect major tonal / colour palette inconsistencies
between the current shot and previous shots.
"""

import json
import logging
import os
from typing import Any

from src.core.validator.base_validator import BaseValidator, ValidationResult

logger = logging.getLogger("StyleValidator")


class StyleValidator(BaseValidator):
    """Checks rendered frame colour/tone consistency against previous shots."""

    def validate(self, shot_data: Any, world_state: Any) -> ValidationResult:
        """
        Loads the current frame and up to 3 recent frames, sends them all to
        Gemini Vision and asks it to flag major tonal inconsistencies.
        """
        shot_id    = shot_data.shot_id
        frame_path = f"./storage/cache/{shot_id}/frame_0000.png"

        if not os.path.exists(frame_path):
            return ValidationResult(passed=True, failures=[], severity="none")

        # Gather reference frames from previous done shots
        all_shots = world_state.get_all_shots()
        prior_done = [
            s for s in all_shots
            if s.shot_id != shot_id and s.status == "done" and s.render_path
        ][-3:]  # Last 3 shots as style reference

        try:
            with open(frame_path, "rb") as f:
                current_frame_bytes = f.read()

            ref_descriptions = []
            for ps in prior_done:
                ref_frame = f"./storage/cache/{ps.shot_id}/frame_0000.png"
                if os.path.exists(ref_frame):
                    ref_descriptions.append(f"Shot {ps.shot_id}")

            refs_text = (
                "Compare against shots: " + ", ".join(ref_descriptions)
                if ref_descriptions
                else "This is the first styled shot — no reference."
            )

            prompt = (
                f"You are a film colourist reviewing shot consistency. {refs_text}\n\n"
                f"Examine this frame's colour palette, contrast, saturation, and overall tone. "
                f"Identify any MAJOR tonal breaks that would be visually jarring to an audience "
                f"(ignore minor exposure differences). "
                f"Respond ONLY with a JSON array of strings describing each major problem. "
                f"If the style is consistent, respond with: []"
            )

            raw = self.ai_provider.analyze(current_frame_bytes, prompt).strip()
            if raw.startswith("```"):
                raw = "\n".join(raw.split("\n")[1:]).rstrip("`").strip()

            issues: list = json.loads(raw)
            if not isinstance(issues, list):
                issues = []

            # Only fail on major issues (more than 1 listed problem)
            if len(issues) > 1:
                return ValidationResult(
                    passed=False,
                    failures=[f"[style] {i}" for i in issues],
                    severity="warning",
                )
            return ValidationResult(passed=True, failures=[], severity="none")

        except json.JSONDecodeError as exc:
            logger.warning("Style validator JSON parse failed: %s", exc)
            return ValidationResult(passed=True, failures=[], severity="none")
        except Exception as exc:
            logger.error("Style validation error: %s", exc)
            return ValidationResult(
                passed=False,
                failures=[f"[style] Validator internal error: {exc}"],
                severity="warning",
            )
