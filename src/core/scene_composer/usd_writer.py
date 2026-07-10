"""
USD Writer — generates minimal valid .usda scene files.
Characters input is now a list of dicts (matching scene_composer output).
"""
from pathlib import Path
from typing import Dict, Any, List


class USDWriter:
    """Writes .usda ASCII scene files for inter-tool scene exchange."""

    @staticmethod
    def write_usda_scene(filepath: str, scene_data: Dict[str, Any]) -> str:
        """Build and write a minimal valid .usda file from scene_data dict."""
        cam = scene_data.get("camera", {})
        light = scene_data.get("lighting", {})

        usda = f"""#usda 1.0
(
    doc = "AI Production Studio — Generated Scene"
    metersPerUnit = 1.0
    upAxis = "Y"
)

def Camera "MainCamera"
{{
    double focalLength = {cam.get("focal_length", 50.0)}
    float3 xformOp:translate = ({cam.get("x", 0.0)}, {cam.get("y", 1.7)}, {cam.get("z", 5.0)})
    float xformOp:rotateX:pitch = {cam.get("pitch", 0.0)}
    uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateX:pitch"]
}}

def DomeLight "MainLight"
{{
    float intensity = {light.get("energy", 1.0)}
}}

"""
        # Characters is a list of dicts [{name, x, y, z, mesh_path}, ...]
        characters: List[Dict] = scene_data.get("characters", [])
        for char in characters:
            name      = str(char.get("name", "Character")).replace(" ", "_")
            mesh_path = str(char.get("mesh_path", ""))
            x = char.get("x", 0.0)
            y = char.get("y", 0.0)
            z = char.get("z", 0.0)

            if mesh_path:
                usda += f"""def Scope "Character_{name}"
{{
    def Mesh "{name}_Mesh" (
        prepend references = @{mesh_path}@
    )
    {{
        float3 xformOp:translate = ({x}, {y}, {z})
        uniform token[] xformOpOrder = ["xformOp:translate"]
    }}
}}

"""
            else:
                usda += f"""def Sphere "Character_{name}_Placeholder"
{{
    float radius = 0.5
    float3 xformOp:translate = ({x}, {y}, {z})
    uniform token[] xformOpOrder = ["xformOp:translate"]
}}

"""

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(usda)
        return filepath
