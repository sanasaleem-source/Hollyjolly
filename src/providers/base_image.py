"""
Base Image Provider Abstract Interface
"""

from abc import ABC, abstractmethod
from typing import Optional

class BaseImageModel(ABC):
    """Interface for generative image systems."""
    
    @abstractmethod
    def generate(self, prompt: str, style_ref: Optional[str] = None) -> bytes:
        """Generates image file bytes from text descriptor."""
        pass
