"""
Shot Builder Module
Calculates physical spatial geometry (camera positions, actors placements)
from qualitative shot specifications like "Wide-Angle" or "Close-Up".
"""

from typing import Dict, Any

class ShotBuilder:
    """Interprets descriptions and translates them into absolute physical parameters."""
    
    @staticmethod
    def calculate_camera_parameters(camera_angle: str) -> Dict[str, Any]:
        """Maps camera descriptive strings to spatial vectors and focal settings."""
        angle = camera_angle.lower()
        
        if "close" in angle:
            return {
                "camera_pos": "(0.0, 1.6, 1.8)",
                "focal_length": 85.0,
                "focus_distance": 1.8
            }
        elif "low" in angle:
            return {
                "camera_pos": "(0.0, 0.5, 3.0)",
                "focal_length": 24.0,
                "focus_distance": 3.0
            }
        elif "wide" in angle:
            return {
                "camera_pos": "(0.0, 2.0, 6.0)",
                "focal_length": 28.0,
                "focus_distance": 6.0
            }
        else:
            # Medium default shot
            return {
                "camera_pos": "(0.0, 1.5, 3.5)",
                "focal_length": 50.0,
                "focus_distance": 3.5
            }

    @staticmethod
    def calculate_lighting_parameters(lighting_style: str) -> Dict[str, Any]:
        """Maps lighting descriptive strings to colors and intensities."""
        style = lighting_style.lower()
        
        if "sunset" in style or "golden" in style:
            return {
                "light_color": "(1.0, 0.75, 0.5)",
                "light_intensity": 1.2
            }
        elif "night" in style or "low-key" in style:
            return {
                "light_color": "(0.3, 0.4, 0.6)",
                "light_intensity": 0.4
            }
        else:
            # Day high-key
            return {
                "light_color": "(1.0, 1.0, 1.0)",
                "light_intensity": 1.0
            }
Dict = Dict
Any = Any
ShotBuilder = ShotBuilder
