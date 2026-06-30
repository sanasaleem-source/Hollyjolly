"""
Provider Factory — single source of truth for which AI provider gets instantiated.
Reads llm_provider from config: "gemini" | "huggingface" | "ollama"
Every part of the app that needs an LLM/vision provider goes through this factory
so there is never a mismatch between what the UI says is active and what actually runs.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_llm_provider(config: dict):
    """Return the correct provider instance based on config['llm_provider']."""
    provider_type = config.get("llm_provider", "gemini").lower()

    if provider_type == "gemini":
        from src.providers.gemini_provider import GeminiProvider
        return GeminiProvider(config)

    elif provider_type == "huggingface":
        from src.providers.huggingface_provider import HuggingFaceProvider
        return HuggingFaceProvider(config)

    elif provider_type == "ollama":
        from src.providers.ollama_provider import OllamaProvider
        return OllamaProvider(config)

    else:
        logger.warning(f"Unknown llm_provider '{provider_type}' — defaulting to Gemini")
        from src.providers.gemini_provider import GeminiProvider
        return GeminiProvider(config)


def get_vision_provider(config: dict):
    """
    Return the correct vision-capable provider.
    HuggingFace text-only models cannot do vision — fall back to Gemini if a
    free-tier key is present, otherwise validators will skip vision checks safely.
    """
    provider_type = config.get("llm_provider", "gemini").lower()

    if provider_type == "gemini":
        from src.providers.gemini_provider import GeminiProvider
        return GeminiProvider(config)

    elif provider_type == "huggingface":
        # Local text models generally can't do vision.
        # If the user also has a Gemini key configured, use it just for vision validation.
        gemini_key = config.get("gemini_api_key", "")
        if gemini_key and gemini_key != "GEMINI_API_KEY_HERE":
            from src.providers.gemini_provider import GeminiProvider
            logger.info("Using Gemini for vision validation alongside local HuggingFace LLM")
            return GeminiProvider(config)
        from src.providers.huggingface_provider import HuggingFaceProvider
        return HuggingFaceProvider(config)  # .analyze() returns safe default

    elif provider_type == "ollama":
        from src.providers.ollama_provider import OllamaProvider
        return OllamaProvider(config)

    from src.providers.gemini_provider import GeminiProvider
    return GeminiProvider(config)


def validate_provider_config(config: dict) -> tuple[bool, str]:
    """
    Check the active provider has what it needs to run.
    Returns (is_valid, message).
    """
    provider_type = config.get("llm_provider", "gemini").lower()

    if provider_type == "gemini":
        key = config.get("gemini_api_key", "")
        if not key or key == "GEMINI_API_KEY_HERE":
            return False, "Gemini selected but no API key is set."
        return True, "Gemini configured."

    elif provider_type == "huggingface":
        repo_id = config.get("hf_repo_id", "")
        if not repo_id:
            return False, "Local model selected but no HuggingFace repo ID is set."
        return True, f"Local model configured: {repo_id}"

    elif provider_type == "ollama":
        return True, "Ollama configured (assumes local server is running)."

    return False, f"Unknown provider: {provider_type}"
