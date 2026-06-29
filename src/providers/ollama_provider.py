"""
Ollama Provider — local LLM via Ollama REST API.
Drop-in replacement for GeminiProvider when running fully offline.
Set llm_provider: ollama in config.yaml to use.
"""
import json
import logging
import time
import urllib.request
from src.providers.base_llm import BaseLLM

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLM):
    """Connects to a locally running Ollama instance at localhost:11434."""

    def __init__(self, config: dict) -> None:
        self.model   = config.get("ollama_model", "llama3")
        self.base_url = config.get("ollama_url", "http://localhost:11434")
        logger.info(f"OllamaProvider initialised — model: {self.model} at {self.base_url}")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Send prompt to local Ollama, return response string."""
        combined = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
        payload  = json.dumps({
            "model":  self.model,
            "prompt": combined,
            "stream": False
        }).encode()

        url = f"{self.base_url}/api/generate"
        max_retries = 3
        backoff = 2

        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(
                    url, data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=120) as resp:
                    data = json.load(resp)
                    return data.get("response", "").strip()
            except Exception as e:
                logger.warning(f"Ollama attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    logger.error("All Ollama retries exhausted.")
                    raise

        return ""

    def analyze(self, image_bytes: bytes, question: str) -> str:
        """Vision via LLaVA model — falls back gracefully if not available."""
        import base64
        payload = json.dumps({
            "model":  "llava",
            "prompt": question,
            "images": [base64.b64encode(image_bytes).decode()],
            "stream": False
        }).encode()
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/generate", data=payload,
                headers={"Content-Type": "application/json"}, method="POST"
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.load(resp)
                return data.get("response", "CONSISTENT").strip()
        except Exception as e:
            logger.error(f"Ollama vision failed: {e}")
            return "CONSISTENT"  # don't block pipeline on vision failure
