"""
Story Parser — parses user prompt into structured ProductionPlan using Gemini.
Uses centralised prompts from src/providers/prompts.py.
"""
import json
import logging
import re
from typing import List, Optional
from pydantic import BaseModel, Field
from src.providers.prompts import DIRECTOR_SYSTEM, DIRECTOR_USER

logger = logging.getLogger(__name__)


class ShotPlan(BaseModel):
    shot_id: str
    scene_id: str
    description: str
    camera_angle: str
    duration_seconds: float
    lighting: str
    characters_present: List[str] = Field(default_factory=list)
    objects_present: List[str] = Field(default_factory=list)
    dialogue: Optional[str] = None
    action: str


class ProductionPlan(BaseModel):
    title: str
    shots: List[ShotPlan]


class StoryParser:
    """Uses Gemini via centralised prompts to parse story into ShotPlans."""

    def __init__(self, provider) -> None:
        self.provider = provider

    def parse_story(self, prompt: str, world_context: str) -> ProductionPlan:
        """Send prompt + world context to Gemini, return validated ProductionPlan."""
        system = DIRECTOR_SYSTEM
        user   = DIRECTOR_USER.format(
            world_context=world_context or "No prior context — this is the first shot.",
            story_prompt=prompt
        )

        raw = self.provider.generate(system, user)
        return self._parse_response(raw, prompt)

    def _parse_response(self, raw: str, original_prompt: str) -> ProductionPlan:
        """Parse and validate Gemini JSON response into ProductionPlan."""
        # Strip markdown fences if present
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()

        try:
            return ProductionPlan.model_validate_json(cleaned)
        except Exception as e:
            logger.warning(f"Direct parse failed ({e}) — attempting JSON extraction")
            # Try extracting JSON object from within the response
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    return ProductionPlan.model_validate_json(match.group())
                except Exception as e2:
                    logger.error(f"JSON extraction also failed: {e2}")

            # Last resort: return a minimal fallback plan so the pipeline doesn't crash
            logger.error("Falling back to minimal production plan")
            return ProductionPlan(
                title="Untitled Production",
                shots=[ShotPlan(
                    shot_id="shot_001",
                    scene_id="scene_001",
                    description=original_prompt[:200],
                    camera_angle="Medium",
                    duration_seconds=4.0,
                    lighting="High-Key",
                    characters_present=[],
                    objects_present=[],
                    action="Scene opens."
                )]
            )
