"""
Base Validator — abstract interface all validators implement.
"""
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import List


class ValidationResult(BaseModel):
    passed: bool
    failures: List[str] = []
    severity: str = "none"  # none | warning | error


class BaseValidator(ABC):
    """Every validator checks exactly one thing."""

    @abstractmethod
    def validate(self, shot_data: dict, world_state) -> ValidationResult:
        """Run validation. Return ValidationResult."""
        ...
