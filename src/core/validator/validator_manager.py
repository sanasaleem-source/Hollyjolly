"""
Validator Manager — runs all validators in sequence for a shot.
"""
import logging
from src.core.validator.character_validator import CharacterValidator
from src.core.validator.story_validator import StoryValidator
from src.core.validator.style_validator import StyleValidator
from src.core.validator.physics_validator import PhysicsValidator
from src.core.validator.base_validator import ValidationResult

logger = logging.getLogger(__name__)


class ValidatorManager:
    """Runs all validators in sequence. Returns combined result."""

    def __init__(self, llm_provider, vision_provider) -> None:
        self.validators = [
            ("character", CharacterValidator(vision_provider)),
            ("story",     StoryValidator(llm_provider)),
            ("style",     StyleValidator(vision_provider)),
            ("physics",   PhysicsValidator(vision_provider)),
        ]

    def validate_shot(self, shot_data: dict, world_state) -> dict:
        """
        Run all validators. Return dict of {validator_name: ValidationResult}.
        """
        results = {}
        for name, validator in self.validators:
            logger.info(f"Running {name} validator for shot {shot_data.get('shot_id')}")
            result = validator.validate(shot_data, world_state)
            results[name] = result
            if not result.passed:
                logger.warning(f"{name} validator FAILED: {result.failures}")
        return results

    def all_passed(self, results: dict) -> bool:
        return all(r.passed for r in results.values())

    def get_failures(self, results: dict) -> dict:
        return {k: v for k, v in results.items() if not v.passed}
