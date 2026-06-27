"""
Continuity Module
Ensures characters, objects, and world state variables remain uniform across shots.
Reads current states from the database to build prompts for model guidance.
"""

import json
from typing import Dict, Any

class ContinuityAdvisor:
    """Provides structured prompts and constraints to preserve story continuity."""
    
    def __init__(self, world_state_manager) -> None:
        """Initializes with the unified World State manager."""
        self.world_state = world_state_manager

    def compile_continuity_context(self) -> str:
        """
        Reads from World State database and builds a text-based continuity guide for the Director.
        """
        # Fetch all characters
        characters = self.world_state.get_all_characters()
        objects = self.world_state.get_all_objects()
        world_events = self.world_state.get_world_events()
        
        context_dict: Dict[str, Any] = {
            "characters": [],
            "objects": [],
            "environment": {}
        }
        
        for char in characters:
            context_dict["characters"].append({
                "name": char.name,
                "appearance": char.appearance,
                "clothing": char.clothing,
                "injuries": char.injuries,
                "relationships": char.relationships,
                "last_seen_shot": char.last_seen_shot_id
            })
            
        for obj in objects:
            context_dict["objects"].append({
                "name": obj.name,
                "condition": obj.condition,
                "location": obj.location,
                "version": obj.version
            })
            
        if world_events:
            # Get latest world setting
            latest = world_events[-1]
            context_dict["environment"] = {
                "time_of_day": latest.time_of_day,
                "weather": latest.weather,
                "lighting": latest.lighting,
                "damage_state": latest.damage_state
            }
            
        return json.dumps(context_dict, indent=2)
