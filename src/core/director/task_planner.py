"""
Task Planner Module
Converts structured shots into a flat, ordered task list for the Orchestrator queue.
"""

from typing import List, Dict, Any
from src.core.director.story_parser import ProductionPlan, ShotPlan

class TaskPlanner:
    """Schedules rendering, asset creation, and validation tasks from a ProductionPlan."""
    
    @staticmethod
    def plan_tasks(production_plan: ProductionPlan) -> List[Dict[str, Any]]:
        """
        Converts a multi-shot ProductionPlan into a list of tasks.
        Each task is a structured dictionary processed sequentially by the Orchestrator.
        """
        tasks = []
        for shot in production_plan.shots:
            # Task 1: Asset Preparation
            tasks.append({
                "task_id": f"task_{shot.shot_id}_assets",
                "shot_id": shot.shot_id,
                "type": "asset_resolution",
                "description": f"Resolve/generate assets for shot {shot.shot_id}",
                "data": {
                    "characters": shot.characters_present,
                    "objects": shot.objects_present,
                    "lighting": shot.lighting
                }
            })
            
            # Task 2: Scene Composition & USD generation
            tasks.append({
                "task_id": f"task_{shot.shot_id}_compose",
                "shot_id": shot.shot_id,
                "type": "scene_composition",
                "description": f"Compose USD and JSON scene for shot {shot.shot_id}",
                "data": {
                    "camera_angle": shot.camera_angle,
                    "characters": shot.characters_present,
                    "objects": shot.objects_present,
                    "action": shot.action
                }
            })
            
            # Task 3: Headless Rendering
            tasks.append({
                "task_id": f"task_{shot.shot_id}_render",
                "shot_id": shot.shot_id,
                "type": "scene_rendering",
                "description": f"Spawn Headless Godot to render shot {shot.shot_id}",
                "data": {
                    "duration": shot.duration_seconds
                }
            })
            
            # Task 4: Pipeline Validation
            tasks.append({
                "task_id": f"task_{shot.shot_id}_validate",
                "shot_id": shot.shot_id,
                "type": "shot_validation",
                "description": f"Run character, story, style, and physics validators on shot {shot.shot_id}",
                "data": {
                    "shot_ref": shot
                }
            })
            
        return tasks
List = List
Dict = Dict
Any = Any
ProductionPlan = ProductionPlan
ShotPlan = ShotPlan
