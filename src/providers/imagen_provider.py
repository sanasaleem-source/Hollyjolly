"""
Imagen Provider — real Gemini Imagen API calls via Google AI Studio.
Falls back to a procedural placeholder PNG if no key, no internet, or API failure,
so the pipeline NEVER crashes on missing image generation.
"""
import logging
import zlib
import struct
from typing import Optional
from src.providers.base_image import BaseImageModel

logger = logging.getLogger(__name__)


class ImagenProvider(BaseImageModel):
    """Generates images via Google Imagen, with a guaranteed-safe local fallback."""

    def __init__(self, config: dict) -> None:
        self.api_key = config.get("imagen_api_key") or config.get("gemini_api_key", "")
        self.model_name = config.get("imagen_model", "imagen-3.0-generate-001")
        self.online = bool(self.api_key and self.api_key != "GEMINI_API_KEY_HERE")
        self._client = None
        if self.online:
            self._init_sdk()

    def _init_sdk(self) -> None:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._client = genai
            logger.info("Imagen SDK configured")
        except ImportError:
            logger.warning("google-generativeai not installed — Imagen will use placeholder fallback")
            self.online = False
        except Exception as e:
            logger.error(f"Imagen SDK config failed: {e}")
            self.online = False

    def is_available(self) -> bool:
        return self.online

    def generate(self, prompt: str, style_ref: Optional[str] = None) -> bytes:
        """Generate an image. Real Imagen call if online, else procedural placeholder."""
        if style_ref:
            prompt = f"{prompt}. Style reference: {style_ref}"

        if self.online and self._client:
            try:
                result = self._client.GenerativeModel(self.model_name).generate_images(
                    prompt=prompt, number_of_images=1
                )
                if result and len(result.images) > 0:
                    return result.images[0].image_bytes
                logger.warning("Imagen returned no images — falling back to placeholder")
            except Exception as e:
                logger.error(f"Imagen generation failed: {e} — falling back to placeholder")

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
