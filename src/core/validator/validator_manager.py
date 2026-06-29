"""
Validator Manager — runs all four validators in sequence for a shot.
"""
import logging
from src.core.validator.character_validator import CharacterValidator
from src.core.validator.story_validator import StoryValidator
from src.core.validator.style_validator import StyleValidator
from src.core.validator.physics_validator import PhysicsValidator
from src.core.validator.base_validator import ValidationResult

logger = logging.getLogger(__name__)


class ValidatorManager:
    """Runs all validators in sequence. Provides unified result dict."""

    def __init__(self, llm_provider, vision_provider) -> None:
        self.validators = [
            ("character", CharacterValidator(vision_provider)),
            ("story",     StoryValidator(llm_provider)),
            ("style",     StyleValidator(vision_provider)),
            ("physics",   PhysicsValidator(vision_provider)),
        ]

    def validate_shot(self, shot_data: dict, world_state) -> dict:
        """Run all validators. Return {name: ValidationResult} dict."""
        results = {}
        for name, validator in self.validators:
            logger.info(f"Running {name} validator for shot {shot_data.get('shot_id')}")
            result = validator.validate(shot_data, world_state)
            results[name] = result
            if not result.passed:
                logger.warning(f"{name} FAILED: {result.failures}")
        return results

    # Alias used by orchestrator/task_runner
    def run_all_validators(self, shot_model, world_state) -> dict:
        """Alias for compatibility — converts ShotModel to dict then runs all validators."""
        shot_data = shot_model.model_dump() if hasattr(shot_model, "model_dump") else dict(shot_model)
        results   = self.validate_shot(shot_data, world_state)
        passed    = all(r.passed for r in results.values())
        failures  = []
        for r in results.values():
            failures.extend(r.failures)
        return {
            "passed":   passed,
            "failures": failures,
            "details":  {k: v.model_dump() for k, v in results.items()}
        }

    def all_passed(self, results: dict) -> bool:
        return results.get("passed", True)

    def get_failures(self, results: dict) -> list:
        return results.get("failures", [])
