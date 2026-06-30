"""
Diffusers Provider — local image generation using any HuggingFace diffusion model.
User pastes a HF repo ID for a text-to-image model (e.g. "stabilityai/sdxl-turbo").
Runs fully offline once downloaded. No API key required.
"""
import logging
from pathlib import Path
from io import BytesIO
from typing import Optional
from src.providers.base_image import BaseImageModel

logger = logging.getLogger(__name__)


class DiffusersProvider(BaseImageModel):
    """Runs a local Stable Diffusion-family model via the diffusers library."""

    def __init__(self, config: dict) -> None:
        self.repo_id   = config.get("hf_image_repo_id", "")
        self.cache_dir = Path(config.get("storage_path", "./storage")) / "models"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.device    = config.get("hf_device", "auto")
        self._pipe     = None

    def is_available(self) -> bool:
        return bool(self.repo_id)

    def is_downloaded(self) -> bool:
        if not self.repo_id:
            return False
        try:
            from huggingface_hub import scan_cache_dir
            cache_info = scan_cache_dir(cache_dir=str(self.cache_dir))
            return any(repo.repo_id == self.repo_id for repo in cache_info.repos)
        except Exception:
            return False

    def download(self, progress_callback=None) -> bool:
        if not self.repo_id:
            return False
        try:
            from huggingface_hub import snapshot_download
            if progress_callback:
                progress_callback(0.0, f"Downloading {self.repo_id}...")
            snapshot_download(repo_id=self.repo_id, cache_dir=str(self.cache_dir), resume_download=True)
            if progress_callback:
                progress_callback(100.0, "Download complete.")
            return True
        except Exception as e:
            logger.error(f"Diffusion model download failed: {e}")
            if progress_callback:
                progress_callback(-1.0, f"Download failed: {e}")
            return False

    def _load(self) -> bool:
        if self._pipe is not None:
            return True
        if not self.repo_id:
            return False
        try:
            import torch
            from diffusers import AutoPipelineForText2Image

            device = "cuda" if (self.device == "auto" and torch.cuda.is_available()) else (
                "cpu" if self.device == "auto" else self.device
            )
            dtype = torch.float16 if device == "cuda" else torch.float32

            self._pipe = AutoPipelineForText2Image.from_pretrained(
                self.repo_id, cache_dir=str(self.cache_dir), torch_dtype=dtype
            )
            self._pipe = self._pipe.to(device)
            logger.info(f"Diffusion model loaded: {self.repo_id} on {device}")
            return True
        except Exception as e:
            logger.error(f"Failed to load diffusion model {self.repo_id}: {e}")
            return False

    def generate(self, prompt: str, style_ref: Optional[str] = None) -> bytes:
        if not self._load():
            raise RuntimeError(f"Could not load local image model: {self.repo_id}")

        full_prompt = f"{prompt}. {style_ref}" if style_ref else prompt
        try:
            image = self._pipe(full_prompt).images[0]
            buf = BytesIO()
            image.save(buf, format="PNG")
            return buf.getvalue()
        except Exception as e:
            logger.error(f"Local image generation failed: {e}")
            raise

    def unload(self) -> None:
        import gc
        self._pipe = None
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
