"""
Story Parser Module
Parses raw user stories or prompts into structured scenes and shots using LLM models.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

class ShotPlan(BaseModel):
    """Pydantic representation of a single planned video shot."""
    shot_id: str = Field(description="Unique identifier for the shot (e.g. shot_001)")
    scene_id: str = Field(description="Unique identifier for the scene this shot belongs to")
    description: str = Field(description="Visual and action details of the shot")
    camera_angle: str = Field(description="The camera perspective or angle, e.g., Wide, Close-Up, Low-Angle")
    duration_seconds: float = Field(description="Duration of the shot in seconds")
    lighting: str = Field(description="Lighting style or environment illumination, e.g., Golden Hour, High-Key, Low-Key")
    characters_present: List[str] = Field(default_factory=list, description="List of characters appearing in this shot")
    objects_present: List[str] = Field(default_factory=list, description="List of prominent props/objects in this shot")
    dialogue: Optional[str] = Field(None, description="Spoken dialogue in the shot, if any")
    action: str = Field(description="Primary motion/action occurring within this shot")

class ProductionPlan(BaseModel):
    """Pydantic representation of the overall multi-shot production workflow."""
    title: str = Field(description="A descriptive title for the generated sequence")
    shots: List[ShotPlan] = Field(description="Sequential list of shots comprising the video production")

class StoryParser:
    """Uses LLM Provider to parse user's narrative input into structured ShotPlans."""
    
    def __init__(self, provider) -> None:
        """Initializes the parser with an AI LLM provider instance."""
        self.provider = provider

    def parse_story(self, prompt: str, world_context: str) -> ProductionPlan:
        """
        Sends the user story and world state to Gemini and structures it into a ProductionPlan.
        
        :param prompt: The raw user prompt detailing the plot.
        :param world_context: A serialized JSON string of the current known World State.
        :return: A parsed and validated ProductionPlan object.
        """
        system_prompt = (
            "You are an expert film director and storyboard planner. Your job is to parse a story prompt "
            "into a detailed sequential list of film shots. You must respect the current World State "
            "context for continuity. All output MUST strictly follow the provided JSON schema."
        )
        
        user_prompt = (
            f"Current World State Context:\n{world_context}\n\n"
            f"Story Prompt:\n{prompt}\n\n"
            "Produce a structured JSON output of the ProductionPlan. Do not include any chat formatting, "
            "preambles, or markdown wrappers. Only valid JSON."
        )
        
        # In a real pipeline, we call the LLM provider and parse with Pydantic
        raw_response = self.provider.generate(system_prompt, user_prompt)
        
        try:
            # Parse and validate using Pydantic
            plan = ProductionPlan.model_validate_json(raw_response)
            return plan
        except Exception as e:
            # Fallback or raising error for orchestrator to handle
            raise ValueError(f"Failed to validate production plan JSON: {e}\nRaw output: {raw_response}")
BaseModel = BaseModel
Field = Field
List = List
Optional = Optional
