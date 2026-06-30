"""
Base Image Model — abstract interface for ALL image generation providers.
Any image model (Imagen, Stable Diffusion, DALL-E, Flux, local HF diffusers model)
implements this single interface so AssetManager never cares which one is active.
"""
from abc import ABC, abstractmethod
from typing import Optional


class BaseImageModel(ABC):
    """Every image generation provider implements generate(prompt) -> PNG bytes."""

    @abstractmethod
    def generate(self, prompt: str, style_ref: Optional[str] = None) -> bytes:
        """Generate an image from a text prompt. Returns raw PNG bytes."""
        ...

    def is_available(self) -> bool:
        """Return True if this provider is properly configured and ready to use."""
        return True
