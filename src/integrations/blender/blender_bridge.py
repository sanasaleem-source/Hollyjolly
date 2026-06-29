"""
Blender Bridge — spawns Blender headless for asset rigging and 3D work.
"""
import json
import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class BlenderBridge:
    """Manages headless Blender sessions for asset creation and rigging."""

    def __init__(self, process_manager, config: dict) -> None:
        self.pm = process_manager
        self.blender_path = config.get("blender_path", "blender")
        self.scripts_dir = Path(__file__).parent / "scripts"
        self.scripts_dir.mkdir(exist_ok=True)

    def rig_mesh(self, mesh_filepath: str, output_path: str) -> str:
        """
        Apply basic auto-rigging to a mesh file.
        Returns path to rigged .blend file.
        """
        script = self._write_rig_script(mesh_filepath, output_path)
        cmd = [self.blender_path, "--background", "--python", script]
        result = self.pm.run_process(cmd, timeout_sec=120)
        if result.returncode != 0:
            logger.error(f"Blender rig failed:\n{result.stderr}")
            return ""
        logger.info(f"Rigged mesh saved: {output_path}")
        return output_path

    def bake_simulation(self, blend_filepath: str, output_path: str) -> str:
        """Bake cloth/hair simulation in a .blend file."""
        script = self._write_bake_script(blend_filepath, output_path)
        cmd = [self.blender_path, "--background", blend_filepath, "--python", script]
        result = self.pm.run_process(cmd, timeout_sec=300)
        if result.returncode != 0:
            logger.error(f"Blender bake failed:\n{result.stderr}")
            return ""
        return output_path

    def export_glb(self, blend_filepath: str, output_path: str) -> str:
        """Export a .blend file to .glb for Godot import."""
        script_content = f"""
import bpy
bpy.ops.wm.open_mainfile(filepath=r"{blend_filepath}")
bpy.ops.export_scene.gltf(filepath=r"{output_path}", export_format="GLB")
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(script_content)
            script = f.name
        cmd = [self.blender_path, "--background", "--python", script]
        result = self.pm.run_process(cmd, timeout_sec=120)
        if result.returncode != 0:
            logger.error(f"GLB export failed:\n{result.stderr}")
            return ""
        return output_path

    def _write_rig_script(self, mesh_path: str, output_path: str) -> str:
        content = f"""
import bpy
bpy.ops.wm.read_homefile(use_empty=True)
bpy.ops.import_scene.obj(filepath=r"{mesh_path}")
for obj in bpy.context.selected_objects:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.armature_add()
bpy.ops.wm.save_as_mainfile(filepath=r"{output_path}")
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            return f.name

    def _write_bake_script(self, blend_path: str, output_path: str) -> str:
        content = f"""
import bpy
bpy.ops.ptcache.bake_all(bake=True)
bpy.ops.wm.save_as_mainfile(filepath=r"{output_path}")
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            return f.name
