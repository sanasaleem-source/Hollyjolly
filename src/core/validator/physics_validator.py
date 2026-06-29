"""
Physics Validator — checks for obvious physics violations in rendered frames.
Uses Gemini Vision.
"""
import logging
from pathlib import Path
from src.core.validator.base_validator import BaseValidator, ValidationResult

logger = logging.getLogger(__name__)


class PhysicsValidator(BaseValidator):
    """Validates basic physics sanity using Gemini Vision."""

    def __init__(self, vision_provider) -> None:
        self.vision = vision_provider

    def validate(self, shot_data: dict, world_state) -> ValidationResult:
        render_path = shot_data.get("render_path", "")
        frame_path = self._find_first_frame(render_path)

        if not frame_path:
            return ValidationResult(passed=True)

        question = (
            "Check this image for obvious physics violations such as: "
            "characters floating above the ground, objects clipping through surfaces, "
            "impossible body positions, or anything that looks physically impossible. "
            "If everything looks physically plausible, reply: PHYSICS_OK. "
            "Otherwise describe the violation."
        )

        try:
            with open(frame_path, "rb") as f:
                image_bytes = f.read()
            result = self.vision.analyze(image_bytes, question)
            if "PHYSICS_OK" in result.upper():
                return ValidationResult(passed=True)
            return ValidationResult(passed=False, failures=[result.strip()], severity="warning")
        except Exception as e:
            logger.error(f"Physics validation failed: {e}")
            return ValidationResult(passed=True)

    def _find_first_frame(self, render_path: str) -> str | None:
        if not render_path:
            return None
        frames = sorted(Path(render_path).glob("frame_*.png"))
        return str(frames[0]) if frames else None
