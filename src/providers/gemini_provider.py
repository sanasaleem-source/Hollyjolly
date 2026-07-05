"""
Gemini Provider — uses the current google-genai SDK (google-genai>=1.0.0).
The old google-generativeai SDK is end-of-life. Do NOT use it.
New API: from google import genai; client = genai.Client(api_key=...)
"""
import json
import time
import logging
from src.providers.base_llm import BaseLLM
from src.providers.base_vision import BaseVisionModel


class GeminiProvider(BaseLLM, BaseVisionModel):
    """Google Gemini via the current google-genai SDK."""

    def __init__(self, config: dict) -> None:
        self.api_key    = config.get("gemini_api_key", "")
        self.model_name = config.get("gemini_model", "gemini-flash-latest")
        self.logger     = logging.getLogger("GeminiProvider")
        self._client    = None
        self.online     = False
        self._init_sdk()

    def _init_sdk(self) -> None:
        if not self.api_key or self.api_key == "GEMINI_API_KEY_HERE":
            self.logger.warning("No Gemini API key — running in offline mock mode.")
            return
        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            self.online  = True
            self.logger.info("Gemini SDK (google-genai) configured.")
        except ImportError:
            self.logger.warning("google-genai not installed. Run: pip install google-genai")
        except Exception as e:
            self.logger.error(f"Gemini SDK init failed: {e}")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self.online:
            return self._mock_response(system_prompt, user_prompt)
        contents = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
        max_retries, backoff = 3, 2
        for attempt in range(max_retries):
            try:
                response = self._client.models.generate_content(
                    model=self.model_name, contents=contents
                )
                return response.text.strip()
            except Exception as e:
                self.logger.warning(f"Gemini attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(backoff); backoff *= 2
                else:
                    self.logger.error("All Gemini retries exhausted.")
                    raise
        return ""

    def analyze(self, image_bytes: bytes, question: str) -> str:
        if not self.online:
            return self._mock_vision_response(question)
        try:
            from google.genai import types as gtypes
            part_image = gtypes.Part.from_bytes(data=image_bytes, mime_type="image/png")
            part_text  = gtypes.Part.from_text(text=question)
            response   = self._client.models.generate_content(
                model="gemini-flash-latest",
                contents=[gtypes.Content(parts=[part_image, part_text])]
            )
            return response.text.strip()
        except Exception as e:
            self.logger.error(f"Gemini vision failed: {e}")
            raise

    def _mock_response(self, system_prompt: str, user_prompt: str) -> str:
        sp = (system_prompt or "").lower()
        if "list of shots" in sp or "film director" in sp:
            return self._mock_story_plan(user_prompt)
        if "contradiction" in sp:
            return "NO_CONTRADICTIONS"
        if "corrected shot description" in sp:
            return "The shot continues as described, with the noted issue resolved."
        if "image prompt" in sp:
            return "A consistent depiction of the character matching their established description."
        if "continuity" in sp or "summarise" in sp:
            return "No prior context — this is the beginning of the production."
        return "OK"

    def _mock_vision_response(self, question: str) -> str:
        q = (question or "").lower()
        if "style" in q:   return "STYLE_CONSISTENT"
        if "physics" in q: return "PHYSICS_OK"
        return "CONSISTENT"

    def _mock_story_plan(self, user_prompt: str) -> str:
        topic = "space mission" if "space" in user_prompt.lower() else "detective story"
        plan = {
            "title": f"A Cinematic {topic.title()}",
            "shots": [
                {
                    "shot_id": "shot_001", "scene_id": "scene_001",
                    "description": "Wide establishing shot of the location.",
                    "camera_angle": "Wide", "duration_seconds": 4.5,
                    "lighting": "Low-Key", "characters_present": ["John"],
                    "objects_present": [], "dialogue": None,
                    "action": "John surveys the scene carefully."
                },
                {
                    "shot_id": "shot_002", "scene_id": "scene_001",
                    "description": "Close-up on the protagonist face.",
                    "camera_angle": "Close-Up", "duration_seconds": 3.0,
                    "lighting": "Natural", "characters_present": ["John"],
                    "objects_present": [], "dialogue": "Something is wrong here.",
                    "action": "John narrows his eyes and steps forward."
                }
            ]
        }
        return json.dumps(plan)
