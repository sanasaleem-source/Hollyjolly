"""
Gemini Provider Module
Implements BaseLLM and BaseVisionModel utilizing the official google-generativeai SDK.
Loads API key from config, supporting model aliases and fail-safe retries.

Offline/mock mode (no API key configured) returns prompt-aware responses —
it inspects the system prompt to determine which caller is asking (Director,
StoryValidator, CharacterValidator, RepairEngine, etc.) and returns the correct
shape of mock response for that specific caller, instead of always returning
a story-plan JSON blob regardless of context.
"""

import time
import logging
from typing import Optional
from src.providers.base_llm import BaseLLM
from src.providers.base_vision import BaseVisionModel


class GeminiProvider(BaseLLM, BaseVisionModel):
    """Google Gemini model controller with fail-safe limits and API retry buffers."""

    def __init__(self, config: dict) -> None:
        self.api_key = config.get("gemini_api_key")
        self.model_name = config.get("gemini_model", "gemini-1.5-pro")
        self.logger = logging.getLogger("GeminiProvider")

        self.initialized = False
        self._init_sdk()

    def _init_sdk(self) -> None:
        """Loads and authenticates the google-generativeai module."""
        if not self.api_key or self.api_key == "GEMINI_API_KEY_HERE":
            self.logger.warning("Gemini API key is not configured. Running in offline/mock mode.")
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.genai = genai
            self.initialized = True
            self.logger.info("Gemini SDK configured successfully.")
        except ImportError:
            self.logger.warning("google-generativeai SDK is not installed. Gemini calls will fall back to mocks.")
        except Exception as e:
            self.logger.error(f"Error configuring Gemini SDK: {e}")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generates text using gemini-1.5-pro with automatic exponential retries."""
        self.logger.info(f"Generating content using model: {self.model_name}")

        if not self.initialized:
            self.logger.info("Provider offline. Returning context-aware mock response.")
            return self._mock_response(system_prompt, user_prompt)

        max_retries = 3
        backoff = 2

        for attempt in range(max_retries):
            try:
                model = self.genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=system_prompt
                )
                response = model.generate_content(user_prompt)
                return response.text.strip()
            except Exception as e:
                self.logger.warning(f"Gemini generation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    self.logger.error("All Gemini API retries exhausted.")
                    raise e
        return ""

    def analyze(self, image_bytes: bytes, question: str) -> str:
        """Analyzes an image using Gemini multimodal vision model."""
        self.logger.info("Analyzing image frame with Gemini Vision.")
        if not self.initialized:
            return self._mock_vision_response(question)

        try:
            model = self.genai.GenerativeModel("gemini-1.5-flash")
            image_data = {"mime_type": "image/png", "data": image_bytes}
            response = model.generate_content([image_data, question])
            return response.text.strip()
        except Exception as e:
            self.logger.error(f"Gemini Vision analysis failed: {e}")
            raise e

    # ── Offline mock dispatch ────────────────────────────────────────────────

    def _mock_response(self, system_prompt: str, user_prompt: str) -> str:
        """
        Route to the correct mock shape based on which caller is asking.
        Inspect the system prompt (set by src/providers/prompts.py) to identify the caller,
        since each validator/director/repair module sends a distinct, identifiable system prompt.
        """
        sp = (system_prompt or "").lower()

        if "list of shots" in sp or "film director" in sp:
            return self._mock_story_parser_output(user_prompt)

        elif "continuity" in sp or "summarise story state" in sp:
            return "No prior context available — offline mode."

        elif "contradiction" in sp:
            # StoryValidator — always pass cleanly in offline mode
            return "NO_CONTRADICTIONS"

        elif "corrected shot description" in sp:
            # RepairEngine story repair — echo back something usable, not JSON
            return "The shot continues as previously described, with the noted issue resolved."

        elif "image prompt" in sp:
            # RepairEngine character repair — return a usable image prompt string
            return "A consistent depiction of the character matching their established appearance."

        # Unknown caller — safe default, never echo raw JSON back to a text-expecting caller
        return "OK"

    def _mock_vision_response(self, question: str) -> str:
        """
        Route to the correct success token based on which validator is asking,
        so offline mode always passes vision checks cleanly instead of returning
        a string that matches none of the expected tokens.
        """
        q = (question or "").lower()

        if "match this description" in q or "character" in q:
            return "CONSISTENT"
        elif "established style" in q or "style" in q:
            return "STYLE_CONSISTENT"
        elif "physics mistakes" in q or "physics" in q:
            return "PHYSICS_OK"

        return "CONSISTENT"  # safe default

    def _mock_story_parser_output(self, user_prompt: str) -> str:
        """Returns valid structured production plan JSON for offline prototyping."""
        topic = "detective story"
        if "rain" in user_prompt.lower():
            topic = "detective story in the rain"
        elif "space" in user_prompt.lower():
            topic = "space cruiser mission"

        return f"""{{
  "title": "A Cinematic {topic.title()}",
  "shots": [
    {{
      "shot_id": "shot_001",
      "scene_id": "scene_001",
      "description": "Establish city streets under a dark rainy sky.",
      "camera_angle": "Wide-Angle",
      "duration_seconds": 4.5,
      "lighting": "Low-Key",
      "characters_present": ["John"],
      "objects_present": ["Umbrella"],
      "action": "John stands on the corner wearing a wet gray coat."
    }},
    {{
      "shot_id": "shot_002",
      "scene_id": "scene_001",
      "description": "Camera moves close to John\'s face, displaying exhaustion.",
      "camera_angle": "Close-Up",
      "duration_seconds": 3.0,
      "lighting": "Golden Hour",
      "characters_present": ["John"],
      "objects_present": [],
      "dialogue": "Another long night in this city...",
      "action": "John sighs, eyes darting to a shadow across the road."
    }}
  ]
}}"""
