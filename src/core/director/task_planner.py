"""
Task Planner — converts a ProductionPlan into an ordered flat task list.
Every task carries all fields the task_runner needs — nothing looked up later.
"""
from typing import List, Dict, Any
from src.core.director.story_parser import ProductionPlan, ShotPlan


class TaskPlanner:
    """Schedules asset, composition, render, and validation tasks per shot."""

    @staticmethod
    def plan_tasks(production_plan: ProductionPlan) -> List[Dict[str, Any]]:
        tasks = []
        for shot in production_plan.shots:

            # ── Task 1: Asset resolution ──────────────────────────────────────
            tasks.append({
                "task_id":     f"task_{shot.shot_id}_assets",
                "shot_id":     shot.shot_id,
                "scene_id":    shot.scene_id,
                "type":        "asset_resolution",
                "description": f"Resolve assets for {shot.shot_id}",
                "data": {
                    "characters": shot.characters_present,
                    "objects":    shot.objects_present,
                    "lighting":   shot.lighting,
                }
            })

            # ── Task 2: Scene composition ─────────────────────────────────────
            # Carries ALL metadata the SceneComposer needs — nothing is missing
            tasks.append({
                "task_id":     f"task_{shot.shot_id}_compose",
                "shot_id":     shot.shot_id,
                "scene_id":    shot.scene_id,
                "type":        "scene_composition",
                "description": f"Compose scene JSON + USD for {shot.shot_id}",
                "data": {
                    "camera_angle":     shot.camera_angle,
                    "lighting":         shot.lighting,
                    "duration_seconds": shot.duration_seconds,
                    "characters":       shot.characters_present,
                    "objects":          shot.objects_present,
                    "action":           shot.action,
                    "description":      shot.description,
                    "dialogue":         shot.dialogue,
                }
            })

            # ── Task 3: Scene rendering ───────────────────────────────────────
            tasks.append({
                "task_id":     f"task_{shot.shot_id}_render",
                "shot_id":     shot.shot_id,
                "scene_id":    shot.scene_id,
                "type":        "scene_rendering",
                "description": f"Render frames for {shot.shot_id}",
                "data": {
                    "duration_seconds": shot.duration_seconds,
                    "description":      shot.description,
                }
            })

            # ── Task 4: Validation ────────────────────────────────────────────
            tasks.append({
                "task_id":     f"task_{shot.shot_id}_validate",
                "shot_id":     shot.shot_id,
                "scene_id":    shot.scene_id,
                "type":        "shot_validation",
                "description": f"Validate {shot.shot_id}",
                "data": {}
            })

        return tasks
