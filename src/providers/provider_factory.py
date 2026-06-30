"""
Provider Factory — single source of truth for which AI provider runs each role.

There are THREE independent model slots, each with its own provider and own API key:
  - text_provider   : story planning, repair text rewriting       (config: text_provider)
  - vision_provider  : validates rendered frames against script    (config: vision_provider)
  - image_provider   : generates character/object/environment art  (config: image_provider)

These are intentionally decoupled. A user might use Gemini for text, a local
HuggingFace model for vision, and Stable Diffusion locally for images — any
combination is valid. Nothing else in the app should construct a provider
directly; everything goes through this factory so the three roles can never
get mismatched.
"""
import logging

logger = logging.getLogger(__name__)

TEXT_PROVIDERS   = {"gemini", "huggingface", "ollama"}
VISION_PROVIDERS = {"gemini", "huggingface", "ollama"}
IMAGE_PROVIDERS  = {"imagen", "diffusers"}


def get_text_provider(config: dict):
    """Return the provider used for story planning, task generation, repair text."""
    provider_type = config.get("text_provider", config.get("llm_provider", "gemini")).lower()

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
        logger.warning(f"Unknown text_provider '{provider_type}' — defaulting to Gemini")
        from src.providers.gemini_provider import GeminiProvider
        return GeminiProvider(config)


def get_vision_provider(config: dict):
    """
    Return the provider used to validate rendered frames.
    Independent API key from text_provider — set vision_gemini_api_key separately
    if you want a different Gemini account/key, or vision_provider: huggingface
    to use a local multimodal model instead.
    """
    provider_type = config.get("vision_provider", config.get("llm_provider", "gemini")).lower()

    if provider_type == "gemini":
        from src.providers.gemini_provider import GeminiProvider
        # Allow a separate key for vision specifically
        vision_config = dict(config)
        if config.get("vision_gemini_api_key"):
            vision_config["gemini_api_key"] = config["vision_gemini_api_key"]
        return GeminiProvider(vision_config)

    elif provider_type == "huggingface":
        from src.providers.huggingface_provider import HuggingFaceProvider
        # Note: most text-only HF models can't do vision — analyze() returns a safe default
        return HuggingFaceProvider(config)

    elif provider_type == "ollama":
        from src.providers.ollama_provider import OllamaProvider
        return OllamaProvider(config)

    from src.providers.gemini_provider import GeminiProvider
    return GeminiProvider(config)


def get_image_provider(config: dict):
    """
    Return the provider used for character/object/environment image generation.
    Independent API key from text_provider — set image_api_key separately.
    """
    provider_type = config.get("image_provider", "imagen").lower()

    if provider_type == "imagen":
        from src.providers.imagen_provider import ImagenProvider
        image_config = dict(config)
        if config.get("image_api_key"):
            image_config["imagen_api_key"] = config["image_api_key"]
        return ImagenProvider(image_config)

    elif provider_type == "diffusers":
        from src.providers.diffusers_provider import DiffusersProvider
        return DiffusersProvider(config)

    else:
        logger.warning(f"Unknown image_provider '{provider_type}' — defaulting to Imagen")
        from src.providers.imagen_provider import ImagenProvider
        return ImagenProvider(config)


def validate_provider_config(config: dict) -> tuple[bool, str]:
    """
    Check that the active TEXT provider has what it needs to run.
    Text is the minimum requirement to use the app at all — vision and image
    providers degrade gracefully (vision skips checks, image falls back to
    a placeholder) so they are not blocking requirements.
    """
    provider_type = config.get("text_provider", config.get("llm_provider", "gemini")).lower()

    if provider_type == "gemini":
        key = config.get("gemini_api_key", "")
        if not key or key == "GEMINI_API_KEY_HERE":
            return False, "Gemini selected for text but no API key is set."
        return True, "Gemini text provider configured."

    elif provider_type == "huggingface":
        repo_id = config.get("hf_repo_id", "")
        if not repo_id:
            return False, "Local model selected for text but no HuggingFace repo ID is set."
        return True, f"Local text model configured: {repo_id}"

    elif provider_type == "ollama":
        return True, "Ollama configured (assumes local server is running)."

    return False, f"Unknown text provider: {provider_type}"


# ── Backward-compatible aliases (old callers used these names) ──
def get_llm_provider(config: dict):
    return get_text_provider(config)
