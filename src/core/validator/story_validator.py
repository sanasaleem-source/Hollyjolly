"""
Story Validator — checks this shot does not contradict earlier events.
Uses Gemini LLM.
"""
import logging
from src.core.validator.base_validator import BaseValidator, ValidationResult

logger = logging.getLogger(__name__)


class StoryValidator(BaseValidator):
    """Validates story continuity using Gemini LLM."""

    def __init__(self, llm_provider) -> None:
        self.llm = llm_provider

    def validate(self, shot_data: dict, world_state) -> ValidationResult:
        shot_id = shot_data.get("shot_id", "unknown")
        description = shot_data.get("description", "")

        history = world_state.get_shot_history()
        if not history:
            return ValidationResult(passed=True)

        history_text = "\n".join(
            f"Shot {s.get('shot_id')}: {s.get('description', '')}"
            for s in history[-10:]  # last 10 shots for context
        )

        system = (
            "You are a story continuity checker. "
            "Given a shot history and a new shot, identify any contradictions. "
            "If none exist, reply exactly: NO_CONTRADICTIONS"
        )
        user = (
            f"Shot history:\n{history_text}\n\n"
            f"New shot {shot_id}: {description}\n\n"
            "List any contradictions, or reply NO_CONTRADICTIONS."
        )

        try:
            result = self.llm.generate(system, user)
            if "NO_CONTRADICTIONS" in result.upper():
                return ValidationResult(passed=True)
            return ValidationResult(
                passed=False,
                failures=[result.strip()],
                severity="error"
            )
        except Exception as e:
            logger.error(f"Story validation failed: {e}")
            return ValidationResult(passed=True)  # don't block on API error
