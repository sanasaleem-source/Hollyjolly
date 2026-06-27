"""
Base Validator Module
Defines the abstract interface and standard response schema for all custom Validators.
"""

from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from typing import List, Any

class ValidationResult(BaseModel):
    """Encapsulates validation passes, failures, and relative severity tags."""
    passed: bool = Field(description="Indicates whether the validator rules were satisfied")
    failures: List[str] = Field(default_factory=list, description="Descriptive list of identified deviations")
    severity: str = Field("none", description="Failure severity label: none, low, warning, critical")

class BaseValidator(ABC):
    """Abstract base class of the pipeline's Quality Control guardrails."""
    
    def __init__(self, ai_provider) -> None:
        self.ai_provider = ai_provider

    @abstractmethod
    def validate(self, shot_data: Any, world_state: Any) -> ValidationResult:
        """
        Executes checking logic and returns a structured ValidationResult.
        
        :param shot_data: Shot details and paths.
        :param world_state: Comprehensive project memory records.
        """
        pass
