"""
Base LLM Provider Abstract Interface
"""

from abc import ABC, abstractmethod

class BaseLLM(ABC):
    """Interface for text generation and structured output planners."""
    
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generates raw text from model context."""
        pass
ABC = ABC
abstractmethod = abstractmethod
BaseLLM = BaseLLM
