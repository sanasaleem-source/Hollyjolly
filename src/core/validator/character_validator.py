"""
Character Validator — checks rendered frames match World State descriptions.
Uses centralised prompts from src/providers/prompts.py.
"""
import json
import logging
from pathlib import Path
from src.core.validator.base_validator import BaseValidator, ValidationResult
from src.providers.prompts import CHARACTER_VALIDATOR_SYSTEM, CHARACTER_VALIDATOR_USER

logger = logging.getLogger(__name__)


class CharacterValidator(BaseValidator):
    """Validates character appearance consistency using Gemini Vision."""

    def __init__(self, vision_provider) -> None:
        self.vision = vision_provider

    def validate(self, shot_data: dict, world_state) -> ValidationResult:
        shot_id    = shot_data.get("shot_id", "unknown")
        render_path = shot_data.get("render_path", "")
        characters  = shot_data.get("characters_present", [])

        if not characters:
            return ValidationResult(passed=True)

        frame_path = self._find_first_frame(render_path)
        if not frame_path:
            logger.warning(f"No frames for {shot_id} — skipping character validation")
            return ValidationResult(passed=True)

        failures = []
        for char_name in characters:
            char = world_state.get_character(char_name)
            if not char:
                continue

            appearance = json.dumps(char.appearance) if isinstance(char.appearance, dict) else str(char.appearance)
            clothing   = json.dumps(char.clothing)   if isinstance(char.clothing,   dict) else str(char.clothing)
            injuries   = json.dumps(char.injuries)   if isinstance(char.injuries,   dict) else str(char.injuries)

            question = CHARACTER_VALIDATOR_USER.format(
                character_name=char_name,
                appearance=appearance,
                clothing=clothing,
                injuries=injuries
            )

            try:
                with open(frame_path, "rb") as f:
                    image_bytes = f.read()
                result = self.vision.analyze(image_bytes, question)
                if "CONSISTENT" not in result.upper():
                    failures.append(f"[character] {char_name}: {result.strip()}")
            except Exception as e:
                logger.error(f"Vision call failed for {char_name}: {e}")

        if failures:
            return ValidationResult(passed=False, failures=failures, severity="error")
        return ValidationResult(passed=True)

    def _find_first_frame(self, render_path: str) -> str | None:
        if not render_path:
            return None
        frames = sorted(Path(render_path).glob("frame_*.png"))
        return str(frames[0]) if frames else None
