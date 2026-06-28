"""
Physics Validator
Uses Gemini Vision to detect obvious physics violations in rendered frames:
floating characters, severe clipping, impossible orientations.
"""

import json
import logging
import os
from typing import Any

from src.core.validator.base_validator import BaseValidator, ValidationResult

logger = logging.getLogger("PhysicsValidator")


class PhysicsValidator(BaseValidator):
    """Catches spatial physics anomalies using Gemini Vision."""

    def validate(self, shot_data: Any, world_state: Any) -> ValidationResult:
        """
        Sends the rendered frame to Gemini Vision and asks it to identify
        any obvious physics impossibilities.
        """
        shot_id    = shot_data.shot_id
        frame_path = f"./storage/cache/{shot_id}/frame_0000.png"

        if not os.path.exists(frame_path):
            return ValidationResult(passed=True, failures=[], severity="none")

        prompt = (
            "You are a 3D scene QA reviewer. Examine this rendered frame for OBVIOUS "
            "physics violations only — for example: characters floating above the ground, "
            "objects intersecting / clipping through walls, characters in anatomically "
            "impossible poses, or elements that clearly defy gravity. "
            "Do NOT report minor rendering imperfections or artistic choices. "
            "Respond ONLY with a valid JSON array of strings describing each violation. "
            "If no violations are detected, respond with: []"
        )

        try:
            with open(frame_path, "rb") as f:
                image_bytes = f.read()

            raw = self.ai_provider.analyze(image_bytes, prompt).strip()
            if raw.startswith("```"):
                raw = "\n".join(raw.split("\n")[1:]).rstrip("`").strip()

            issues: list = json.loads(raw)
            if not isinstance(issues, list):
                issues = []

            if issues:
                return ValidationResult(
                    passed=False,
                    failures=[f"[physics] {i}" for i in issues],
                    severity="warning",
                )
            return ValidationResult(passed=True, failures=[], severity="none")

        except json.JSONDecodeError as exc:
            logger.warning("Physics validator JSON parse failed: %s", exc)
            return ValidationResult(passed=True, failures=[], severity="none")
        except Exception as exc:
            logger.error("Physics validation error: %s", exc)
            return ValidationResult(
                passed=False,
                failures=[f"[physics] Validator internal error: {exc}"],
                severity="warning",
            )
