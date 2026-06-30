"""
Style Validator — checks colour/tone consistency across shots.
Uses centralised, model-neutral prompts and lenient response matching.
"""
import logging
from pathlib import Path
from src.core.validator.base_validator import BaseValidator, ValidationResult
from src.core.validator.response_matching import matches_success_token
from src.providers.prompts import STYLE_VALIDATOR_SYSTEM, STYLE_VALIDATOR_USER

logger = logging.getLogger(__name__)


class StyleValidator(BaseValidator):
    """Validates visual style consistency using a vision-capable provider."""

    def __init__(self, vision_provider) -> None:
        self.vision = vision_provider

    def validate(self, shot_data: dict, world_state) -> ValidationResult:
        render_path = shot_data.get("render_path", "")
        frame_path  = self._find_first_frame(render_path)
        if not frame_path:
            return ValidationResult(passed=True)

        style_ref = world_state.get_style_reference()
        if not style_ref:
            return ValidationResult(passed=True)

        user = STYLE_VALIDATOR_USER.format(style_reference=style_ref)

        try:
            with open(frame_path, "rb") as f:
                image_bytes = f.read()
            result = self.vision.analyze(image_bytes, user)
            if matches_success_token(result, "STYLE_CONSISTENT"):
                return ValidationResult(passed=True)
            return ValidationResult(passed=False, failures=[f"[style] {result.strip()}"], severity="warning")
        except Exception as e:
            logger.error(f"Style validation failed: {e}")
            return ValidationResult(passed=True)

    def _find_first_frame(self, render_path: str) -> str | None:
        if not render_path:
            return None
        frames = sorted(Path(render_path).glob("frame_*.png"))
        return str(frames[0]) if frames else None
