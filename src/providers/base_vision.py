"""
Base Vision Provider Abstract Interface
"""

from abc import ABC, abstractmethod

class BaseVisionModel(ABC):
    """Interface for multimodal analyzing networks."""
    
    @abstractmethod
    def analyze(self, image_bytes: bytes, question: str) -> str:
        """Analyzes an image and answers questions about visual context."""
        pass
