"""
Character Validator — checks rendered frames match World State character descriptions.
Uses Gemini Vision.
"""
import logging
from pathlib import Path
from src.core.validator.base_validator import BaseValidator, ValidationResult

logger = logging.getLogger(__name__)


class CharacterValidator(BaseValidator):
    """Validates character appearance consistency using Gemini Vision."""

    def __init__(self, vision_provider) -> None:
        self.vision = vision_provider

    def validate(self, shot_data: dict, world_state) -> ValidationResult:
        shot_id = shot_data.get("shot_id", "unknown")
        render_path = shot_data.get("render_path", "")
        characters = shot_data.get("characters_present", [])

        if not characters:
            return ValidationResult(passed=True)

        # Find first rendered frame
        frame_path = self._find_first_frame(render_path)
        if not frame_path:
            logger.warning(f"No frames found for shot {shot_id} — skipping character validation")
            return ValidationResult(passed=True)

        failures = []
        for char_name in characters:
            char = world_state.get_character(char_name)
            if not char:
                continue

            description = (
                f"Name: {char_name}\n"
                f"Appearance: {char.get('appearance', 'unknown')}\n"
                f"Clothing: {char.get('clothing', 'unknown')}\n"
                f"Injuries: {char.get('injuries', 'none')}"
            )

            question = (
                f"Does the character in this image match this description?\n{description}\n"
                f"List any inconsistencies. If consistent, reply: CONSISTENT"
            )

            try:
                with open(frame_path, "rb") as f:
                    image_bytes = f.read()
                result = self.vision.analyze(image_bytes, question)
                if "CONSISTENT" not in result.upper():
                    failures.append(f"{char_name}: {result.strip()}")
            except Exception as e:
                logger.error(f"Vision call failed for {char_name}: {e}")

        if failures:
            return ValidationResult(passed=False, failures=failures, severity="error")
        return ValidationResult(passed=True)

    def _find_first_frame(self, render_path: str) -> str | None:
        if not render_path:
            return None
        path = Path(render_path)
        frames = sorted(path.glob("frame_*.png"))
        return str(frames[0]) if frames else None
