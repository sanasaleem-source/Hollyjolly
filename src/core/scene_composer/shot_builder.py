"""
Shot Builder — maps descriptive camera/lighting strings to numeric parameters.
Returns flat dicts with individual keys so scene_composer can build proper JSON.
"""
from typing import Dict, Any


class ShotBuilder:
    """Translates qualitative shot descriptions into numeric scene parameters."""

    @staticmethod
    def calculate_camera_parameters(camera_angle: str) -> Dict[str, Any]:
        """Return camera position and lens settings as individual numeric keys."""
        angle = (camera_angle or "medium").lower()

        if "close" in angle:
            return {"camera_x": 0.0, "camera_y": 1.6, "camera_z": 1.8,
                    "fov": 40.0, "focal_length": 85.0,
                    "pitch": -5.0, "yaw": 0.0}
        elif "low" in angle:
            return {"camera_x": 0.0, "camera_y": 0.4, "camera_z": 3.0,
                    "fov": 75.0, "focal_length": 24.0,
                    "pitch": 20.0, "yaw": 0.0}
        elif "high" in angle:
            return {"camera_x": 0.0, "camera_y": 4.0, "camera_z": 3.0,
                    "fov": 60.0, "focal_length": 35.0,
                    "pitch": -35.0, "yaw": 0.0}
        elif "wide" in angle:
            return {"camera_x": 0.0, "camera_y": 1.8, "camera_z": 6.0,
                    "fov": 75.0, "focal_length": 28.0,
                    "pitch": -5.0, "yaw": 0.0}
        elif "pov" in angle:
            return {"camera_x": 0.0, "camera_y": 1.7, "camera_z": 0.3,
                    "fov": 90.0, "focal_length": 24.0,
                    "pitch": 0.0, "yaw": 0.0}
        else:  # medium default
            return {"camera_x": 0.0, "camera_y": 1.5, "camera_z": 3.5,
                    "fov": 55.0, "focal_length": 50.0,
                    "pitch": -5.0, "yaw": 0.0}

    @staticmethod
    def calculate_lighting_parameters(lighting_style: str) -> Dict[str, Any]:
        """Return light energy, colour, and direction as individual keys."""
        style = (lighting_style or "standard").lower()

        if "golden" in style or "sunset" in style:
            return {"light_intensity": 1.2, "sky_color": "e8a050",
                    "pitch": -20.0, "yaw": 45.0}
        elif "night" in style or "low-key" in style or "dark" in style:
            return {"light_intensity": 0.35, "sky_color": "1a1f35",
                    "pitch": -60.0, "yaw": -30.0}
        elif "overcast" in style or "grey" in style:
            return {"light_intensity": 0.7, "sky_color": "9aa0aa",
                    "pitch": -45.0, "yaw": 0.0}
        elif "rainy" in style or "rain" in style:
            return {"light_intensity": 0.5, "sky_color": "505a6a",
                    "pitch": -50.0, "yaw": 15.0}
        else:  # high-key day
            return {"light_intensity": 1.0, "sky_color": "6a9fd8",
                    "pitch": -45.0, "yaw": 30.0}
