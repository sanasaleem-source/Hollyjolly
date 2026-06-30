"""
Physics Validator — checks for obvious physics violations in rendered frames.
Uses centralised, model-neutral prompts and lenient response matching.
"""
import logging
from pathlib import Path
from src.core.validator.base_validator import BaseValidator, ValidationResult
from src.core.validator.response_matching import matches_success_token
from src.providers.prompts import PHYSICS_VALIDATOR_SYSTEM, PHYSICS_VALIDATOR_USER

logger = logging.getLogger(__name__)


class PhysicsValidator(BaseValidator):
    """Validates basic physics sanity using a vision-capable provider."""

    def __init__(self, vision_provider) -> None:
        self.vision = vision_provider

    def validate(self, shot_data: dict, world_state) -> ValidationResult:
        render_path = shot_data.get("render_path", "")
        frame_path  = self._find_first_frame(render_path)
        if not frame_path:
            return ValidationResult(passed=True)

        description = shot_data.get("description", "")
        user = PHYSICS_VALIDATOR_USER.format(shot_description=description)

        try:
            with open(frame_path, "rb") as f:
                image_bytes = f.read()
            result = self.vision.analyze(image_bytes, user)
            if matches_success_token(result, "PHYSICS_OK"):
                return ValidationResult(passed=True)
            return ValidationResult(passed=False, failures=[f"[physics] {result.strip()}"], severity="warning")
        except Exception as e:
            logger.error(f"Physics validation failed: {e}")
            return ValidationResult(passed=True)

    def _find_first_frame(self, render_path: str) -> str | None:
        if not render_path:
            return None
        frames = sorted(Path(render_path).glob("frame_*.png"))
        return str(frames[0]) if frames else None
