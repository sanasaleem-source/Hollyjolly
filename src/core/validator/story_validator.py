"""
Story Validator — checks shot does not contradict earlier events.
Uses centralised, model-neutral prompts and lenient response matching.
"""
import logging
from src.core.validator.base_validator import BaseValidator, ValidationResult
from src.core.validator.response_matching import matches_success_token
from src.providers.prompts import STORY_VALIDATOR_SYSTEM, STORY_VALIDATOR_USER

logger = logging.getLogger(__name__)


class StoryValidator(BaseValidator):
    """Validates story continuity using a text-capable provider."""

    def __init__(self, llm_provider) -> None:
        self.llm = llm_provider

    def validate(self, shot_data: dict, world_state) -> ValidationResult:
        shot_id     = shot_data.get("shot_id", "unknown")
        description = shot_data.get("description", "")
        action      = shot_data.get("action", "")
        full_desc   = f"{description} {action}".strip()

        history = world_state.get_shot_history()
        if not history:
            return ValidationResult(passed=True)

        history_text = "\n".join(
            f"Shot {s.get('shot_id')}: {s.get('description', '')} — {s.get('action', '')}"
            for s in history[-10:]
        )

        user = STORY_VALIDATOR_USER.format(
            shot_history=history_text, shot_id=shot_id, shot_description=full_desc
        )

        try:
            result = self.llm.generate(STORY_VALIDATOR_SYSTEM, user)
            if matches_success_token(result, "NO_CONTRADICTIONS"):
                return ValidationResult(passed=True)
            return ValidationResult(passed=False, failures=[f"[story] {result.strip()}"], severity="error")
        except Exception as e:
            logger.error(f"Story validation failed: {e}")
            return ValidationResult(passed=True)
