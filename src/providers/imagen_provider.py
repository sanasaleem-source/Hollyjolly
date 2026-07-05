"""
Imagen Provider — real image generation via Google Imagen (google-genai SDK).
Falls back to a procedural placeholder PNG so the pipeline never crashes.
"""
import logging
import zlib, struct
from typing import Optional
from src.providers.base_image import BaseImageModel

logger = logging.getLogger(__name__)


class ImagenProvider(BaseImageModel):
    """Generates images via Google Imagen API with a guaranteed-safe local fallback."""

    def __init__(self, config: dict) -> None:
        self.api_key    = config.get("imagen_api_key") or config.get("gemini_api_key", "")
        self.model_name = config.get("imagen_model", "imagen-3.0-generate-001")
        self.online     = bool(self.api_key and self.api_key != "GEMINI_API_KEY_HERE")
        self._client    = None
        if self.online:
            self._init_sdk()

    def _init_sdk(self) -> None:
        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            logger.info("Imagen (google-genai) SDK configured.")
        except ImportError:
            logger.warning("google-genai not installed — Imagen will use placeholder fallback.")
            self.online = False
        except Exception as e:
            logger.error(f"Imagen SDK init failed: {e}")
            self.online = False

    def is_available(self) -> bool:
        return self.online

    def generate(self, prompt: str, style_ref: Optional[str] = None) -> bytes:
        if style_ref:
            prompt = f"{prompt}. Style: {style_ref}"
        if self.online and self._client:
            try:
                response = self._client.models.generate_images(
                    model=self.model_name,
                    prompt=prompt,
                    config={"number_of_images": 1}
                )
                if response and response.generated_images:
                    return response.generated_images[0].image.image_bytes
                logger.warning("Imagen returned no images — falling back to placeholder.")
            except Exception as e:
                logger.error(f"Imagen generation failed: {e} — using placeholder.")
        return self._placeholder_png(prompt)

    def _placeholder_png(self, prompt: str) -> bytes:
        """Zero-dependency 256x256 coloured PNG — never breaks the pipeline."""
        w, h   = 256, 256
        ph     = hash(prompt)
        r      = max(50, min((ph & 0xFF0000) >> 16, 220))
        g      = max(50, min((ph & 0x00FF00) >>  8, 220))
        b      = max(50, min( ph & 0x0000FF,        220))
        row    = b"\x00" + struct.pack("BBB", r, g, b) * w
        raw    = row * h
        sig    = b"\x89PNG\r\n\x1a\n"
        def chunk(tag, data):
            c = tag + data
            return struct.pack("!I", len(data)) + c + struct.pack("!I", zlib.crc32(c))
        ihdr = chunk(b"IHDR", struct.pack("!IIBBBBB", w, h, 8, 2, 0, 0, 0))
        idat = chunk(b"IDAT", zlib.compress(raw))
        iend = chunk(b"IEND", b"")
        return sig + ihdr + idat + iend
