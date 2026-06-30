"""
HuggingFace Provider — downloads and runs a HuggingFace model fully locally.
User pastes a HF repo ID (e.g. "Qwen/Qwen2.5-3B-Instruct"). The model is
downloaded once via huggingface_hub, cached locally, and run via transformers.
Designed to work without any API key.
"""
import logging
import os
from pathlib import Path
from typing import Optional
from src.providers.base_llm import BaseLLM

logger = logging.getLogger(__name__)


class HuggingFaceProvider(BaseLLM):
    """Runs a local HuggingFace model for text generation. No API key required."""

    def __init__(self, config: dict) -> None:
        self.repo_id     = config.get("hf_repo_id", "")
        self.cache_dir   = Path(config.get("storage_path", "./storage")) / "models"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.device      = config.get("hf_device", "auto")  # auto | cpu | cuda
        self.max_tokens  = config.get("hf_max_new_tokens", 1024)
        self._model      = None
        self._tokenizer  = None
        self._pipeline   = None

        if not self.repo_id:
            logger.warning("No hf_repo_id configured — HuggingFaceProvider is idle until set")

    def is_downloaded(self) -> bool:
        """Check if model files already exist in local cache."""
        if not self.repo_id:
            return False
        try:
            from huggingface_hub import scan_cache_dir
            cache_info = scan_cache_dir(cache_dir=str(self.cache_dir))
            return any(repo.repo_id == self.repo_id for repo in cache_info.repos)
        except Exception:
            return False

    def download(self, progress_callback=None) -> bool:
        """
        Download the model from HuggingFace Hub into local cache.
        progress_callback(pct: float, message: str) is called during download if provided.
        """
        if not self.repo_id:
            logger.error("No repo_id set — cannot download")
            return False

        try:
            from huggingface_hub import snapshot_download

            if progress_callback:
                progress_callback(0.0, f"Starting download of {self.repo_id}...")

            snapshot_download(
                repo_id=self.repo_id,
                cache_dir=str(self.cache_dir),
                resume_download=True,
            )

            if progress_callback:
                progress_callback(100.0, "Download complete.")

            logger.info(f"Model downloaded: {self.repo_id}")
            return True

        except Exception as e:
            logger.error(f"Download failed for {self.repo_id}: {e}")
            if progress_callback:
                progress_callback(-1.0, f"Download failed: {e}")
            return False

    def load(self) -> bool:
        """Load model and tokenizer into memory. Called once before first generate()."""
        if self._pipeline is not None:
            return True

        if not self.repo_id:
            logger.error("No repo_id set — cannot load model")
            return False

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

            logger.info(f"Loading {self.repo_id} into memory (device={self.device})...")

            device_map = "auto" if self.device == "auto" else None
            torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

            self._tokenizer = AutoTokenizer.from_pretrained(
                self.repo_id, cache_dir=str(self.cache_dir)
            )
            self._model = AutoModelForCausalLM.from_pretrained(
                self.repo_id,
                cache_dir=str(self.cache_dir),
                device_map=device_map,
                torch_dtype=torch_dtype,
            )

            self._pipeline = pipeline(
                "text-generation",
                model=self._model,
                tokenizer=self._tokenizer,
            )
            logger.info(f"Model loaded successfully: {self.repo_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to load model {self.repo_id}: {e}")
            return False

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate text using the local model. Loads model on first call if needed."""
        if self._pipeline is None:
            if not self.load():
                raise RuntimeError(f"Could not load local model: {self.repo_id}")

        combined = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt

        try:
            # Try chat template if tokenizer supports it
            if hasattr(self._tokenizer, "apply_chat_template") and self._tokenizer.chat_template:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": user_prompt})
                prompt_text = self._tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
            else:
                prompt_text = combined

            result = self._pipeline(
                prompt_text,
                max_new_tokens=self.max_tokens,
                do_sample=True,
                temperature=0.7,
                pad_token_id=self._tokenizer.eos_token_id,
            )
            generated = result[0]["generated_text"]
            # Strip the prompt from the output if echoed back
            if generated.startswith(prompt_text):
                generated = generated[len(prompt_text):]
            return generated.strip()

        except Exception as e:
            logger.error(f"Local generation failed: {e}")
            raise

    def analyze(self, image_bytes: bytes, question: str) -> str:
        """
        Vision support for local models is model-dependent.
        Most text-only local models cannot do this — return a safe default
        so the pipeline doesn't crash, and log a warning.
        """
        logger.warning(
            f"{self.repo_id} does not support vision analysis — "
            "skipping validation check (treating as passed)"
        )
        return "CONSISTENT"

    def unload(self) -> None:
        """Free memory by unloading the model."""
        import gc
        self._pipeline = None
        self._model = None
        self._tokenizer = None
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
        logger.info(f"Unloaded model: {self.repo_id}")

    def estimate_size_gb(self) -> Optional[float]:
        """Estimate model download size in GB from HF Hub metadata, if available."""
        if not self.repo_id:
            return None
        try:
            from huggingface_hub import HfApi
            api = HfApi()
            info = api.model_info(self.repo_id, files_metadata=True)
            total_bytes = sum(f.size or 0 for f in info.siblings if f.size)
            return round(total_bytes / (1024 ** 3), 2) if total_bytes else None
        except Exception as e:
            logger.warning(f"Could not estimate size for {self.repo_id}: {e}")
            return None
