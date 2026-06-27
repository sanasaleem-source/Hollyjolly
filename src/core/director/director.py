"""
Director Module Entry Point
Coordinates parsing story prompts, planning workflows, and feeding state continuity details.
"""

from typing import List, Dict, Any
from src.core.director.story_parser import StoryParser, ProductionPlan
from src.core.director.task_planner import TaskPlanner
from src.core.director.continuity import ContinuityAdvisor

class Director:
    """The central creative core. Takes a prompt, outputs a production and task schedule."""
    
    def __init__(self, ai_provider, world_state_manager) -> None:
        """
        Initializes Director with an AI LLM provider and World State manager.
        """
        self.parser = StoryParser(ai_provider)
        self.continuity = ContinuityAdvisor(world_state_manager)
        
    def generate_production_plan(self, story_prompt: str) -> ProductionPlan:
        """
        Gathers continuity context from World State, prompts Gemini to create
        a structured ProductionPlan, and returns it.
        """
        # 1. Compile world context
        world_context = self.continuity.compile_continuity_context()
        
        # 2. Parse story into shots
        production_plan = self.parser.parse_story(story_prompt, world_context)
        
        return production_plan

    def create_task_schedule(self, production_plan: ProductionPlan) -> List[Dict[str, Any]]:
        """
        Converts the ProductionPlan into sequential pipeline tasks.
        """
        return TaskPlanner.plan_tasks(production_plan)
List = List
Dict = Dict
Any = Any
StoryParser = StoryParser
ProductionPlan = ProductionPlan
TaskPlanner = TaskPlanner
ContinuityAdvisor = ContinuityAdvisor
