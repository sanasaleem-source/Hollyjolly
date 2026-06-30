"""
Gemini Image Provider — image generation via Gemini's native image models
("Nano Banana" family) using the current `google-genai` SDK.

Replaces the old ImagenProvider: Google is shutting down the standalone
Imagen endpoint in favor of generating images directly through
client.models.generate_content() on a Gemini image-capable model. This uses
the same generate_content() call path as text, with response_modalities=["IMAGE"].

Falls back to a procedural placeholder PNG if no key, no internet, or API
failure, so the pipeline never crashes on missing image generation.
"""
import logging
import zlib
import struct
from typing import Optional
from src.providers.base_image import BaseImageModel

logger = logging.getLogger(__name__)


class GeminiImageProvider(BaseImageModel):
    """Generates images via Gemini's native image models, with a guaranteed-safe local fallback."""

    def __init__(self, config: dict) -> None:
        self.api_key = config.get("image_api_key") or config.get("gemini_api_key", "")
        # gemini-2.5-flash-image ("Nano Banana") is Google's current recommended
        # replacement for Imagen — fast tier. Use gemini-3-pro-image for higher
        # fidelity/complex-instruction generation at higher latency/cost.
        self.model_name = config.get("gemini_image_model", "gemini-2.5-flash-image")
        self.online = bool(self.api_key and self.api_key != "GEMINI_API_KEY_HERE")
        self.client = None
        if self.online:
            self._init_sdk()

    def _init_sdk(self) -> None:
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            logger.info("Gemini image client configured")
        except ImportError:
            logger.warning("google-genai not installed — image generation will use placeholder fallback")
            self.online = False
        except Exception as e:
            logger.error(f"Gemini image client config failed: {e}")
            self.online = False

    def is_available(self) -> bool:
        return self.online

    def generate(self, prompt: str, style_ref: Optional[str] = None) -> bytes:
        """Generate an image. Real Gemini image call if online, else procedural placeholder."""
        if style_ref:
            prompt = f"{prompt}. Style reference: {style_ref}"

        if self.online and self.client:
            try:
                from google.genai import types
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
                )
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        return part.inline_data.data
                logger.warning("Gemini image call returned no image data — falling back to placeholder")
            except Exception as e:
                logger.error(f"Gemini image generation failed: {e} — falling back to placeholder")

        return self._generate_procedural_png(prompt)

    def _generate_procedural_png(self, prompt: str) -> bytes:
        """Zero-dependency placeholder PNG so the pipeline never breaks on missing image gen."""
        width, height = 256, 256
        prompt_hash = hash(prompt)
        r = max(50, min((prompt_hash & 0xFF0000) >> 16, 220))
        g = max(50, min((prompt_hash & 0x00FF00) >> 8, 220))
        b = max(50, min(prompt_hash & 0x0000FF, 220))

        pixel_byte = struct.pack("BBB", r, g, b)
        row_data = b"\x00" + (pixel_byte * width)
        img_data = row_data * height

        png_signature = b"\x89PNG\r\n\x1a\n"
        ihdr_data = struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0)
        ihdr_chunk = b"IHDR" + ihdr_data
        ihdr = struct.pack("!I", len(ihdr_data)) + ihdr_chunk + struct.pack("!I", zlib.crc32(ihdr_chunk))

        compressed = zlib.compress(img_data)
        idat_chunk = b"IDAT" + compressed
        idat = struct.pack("!I", len(compressed)) + idat_chunk + struct.pack("!I", zlib.crc32(idat_chunk))

        iend_chunk = b"IEND"
        iend = struct.pack("!I", 0) + iend_chunk + struct.pack("!I", zlib.crc32(iend_chunk))

        return png_signature + ihdr + idat + iend


# Backward-compatible alias — keep old import path working for any callers/tests
ImagenProvider = GeminiImageProvider
