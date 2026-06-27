"""
Validator Manager Module
Aggregates all validators and exposes a single API to audit rendered shot data.
"""

from typing import Dict, Any
from src.core.validator.character_validator import CharacterValidator
from src.core.validator.story_validator import StoryValidator
from src.core.validator.style_validator import StyleValidator
from src.core.validator.physics_validator import PhysicsValidator

class ValidatorManager:
    """Manages sequential trigger of style, physics, story, and actor validations."""
    
    def __init__(self, ai_provider) -> None:
        self.validators = [
            CharacterValidator(ai_provider),
            StoryValidator(ai_provider),
            StyleValidator(ai_provider),
            PhysicsValidator(ai_provider)
        ]

    def run_all_validators(self, shot_data: Any, world_state: Any) -> Dict[str, Any]:
        """
        Executes checking workflow. Accumulates failures across components.
        """
        passed = True
        failures = []
        severity = "none"
        
        for validator in self.validators:
            res = validator.validate(shot_data, world_state)
            if not res.passed:
                passed = False
                failures.extend(res.failures)
                if res.severity == "critical":
                    severity = "critical"
                elif res.severity == "warning" and severity != "critical":
                    severity = "warning"
                elif severity == "none":
                    severity = res.severity
                    
        return {
            "passed": passed,
            "failures": failures,
            "severity": severity
        }
