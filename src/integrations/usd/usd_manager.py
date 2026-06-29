"""
USD Manager — read/write OpenUSD scene files via usd-core Python library.
"""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class USDManager:
    """Manages OpenUSD scene files for inter-tool scene exchange."""

    def write_scene(self, scene_data: dict, output_path: str) -> bool:
        """
        Write a USD scene file from scene_data dict.
        Falls back to JSON sidecar if usd-core is not installed.
        """
        try:
            from pxr import Usd, UsdGeom, Gf, Sdf

            stage = Usd.Stage.CreateNew(output_path)
            UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

            # Camera
            cam_data = scene_data.get("camera", {})
            cam = UsdGeom.Camera.Define(stage, "/Scene/Camera")
            cam.GetFocalLengthAttr().Set(cam_data.get("focal_length", 35.0))

            # Characters
            for char in scene_data.get("characters", []):
                xform = UsdGeom.Xform.Define(stage, f"/Scene/Characters/{char['name']}")
                xform.AddTranslateOp().Set(
                    Gf.Vec3d(char.get("x", 0), char.get("y", 0), char.get("z", 0))
                )

            # Environment
            env = UsdGeom.Xform.Define(stage, "/Scene/Environment")

            stage.GetRootLayer().Save()
            logger.info(f"USD scene written: {output_path}")
            return True

        except ImportError:
            logger.warning("usd-core not installed — writing JSON sidecar instead")
            import json
            json_path = output_path.replace(".usda", ".json")
            with open(json_path, "w") as f:
                json.dump(scene_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"USD write failed: {e}")
            return False

    def inspect_stage(self, filepath: str) -> dict:
        """Read a USD file and return basic stage info."""
        try:
            from pxr import Usd
            stage = Usd.Stage.Open(filepath)
            prims = [str(p.GetPath()) for p in stage.Traverse()]
            return {"path": filepath, "prims": prims, "valid": True}
        except Exception as e:
            logger.error(f"USD inspect failed: {e}")
            return {"path": filepath, "valid": False, "error": str(e)}
