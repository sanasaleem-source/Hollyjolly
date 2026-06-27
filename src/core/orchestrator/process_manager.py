"""
Process Manager Module
Safely spawns and tracks subprocess processes for headless Godot, Blender, and FFmpeg.
Never spawns more than one heavy process simultaneously in V1.
"""

import subprocess
import logging
import sys
from typing import List, Optional

class ProcessManager:
    """Manages spawning, execution tracking, and timeout controls for external tools."""
    
    def __init__(self, config: dict) -> None:
        self.config = config
        self.godot_path = config.get("godot_path", "godot")
        self.blender_path = config.get("blender_path", "blender")
        self.ffmpeg_path = config.get("ffmpeg_path", "ffmpeg")
        self.logger = logging.getLogger("ProcessManager")

    def run_process(self, cmd: List[str], timeout_sec: int = 300) -> subprocess.CompletedProcess:
        """
        Runs a command as a blocking subprocess call, enforcing a timeout
        and logging stdout/stderr streams.
        """
        self.logger.info(f"Spawning process: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                check=True
            )
            # Log output summaries
            if result.stdout:
                self.logger.debug(f"Subprocess output: {result.stdout[:500]}...")
            return result
        except subprocess.TimeoutExpired as te:
            self.logger.error(f"Process timed out after {timeout_sec}s: {' '.join(cmd)}")
            raise te
        except subprocess.CalledProcessError as cpe:
            self.logger.error(f"Process failed with exit code {cpe.returncode}")
            self.logger.error(f"Error output: {cpe.stderr}")
            raise cpe
        except Exception as e:
            self.logger.error(f"Unexpected error running process: {e}")
            raise e

    def run_godot_headless(self, scene_script_path: str, output_path: str, timeout: int = 300) -> subprocess.CompletedProcess:
        """Spawns Godot 4 headlessly to execute a rendering script."""
        cmd = [
            self.godot_path,
            "--headless",
            "--script", scene_script_path,
            "--output-dir", output_path
        ]
        return self.run_process(cmd, timeout_sec=timeout)

    def run_blender_headless(self, python_script_path: str, timeout: int = 300) -> subprocess.CompletedProcess:
        """Spawns Blender in background mode to run a Python modelling script."""
        cmd = [
            self.blender_path,
            "--background",
            "--python", python_script_path
        ]
        return self.run_process(cmd, timeout_sec=timeout)

    def run_ffmpeg(self, args: List[str], timeout: int = 300) -> subprocess.CompletedProcess:
        """Spawns FFmpeg tool with arguments for video compilation."""
        cmd = [self.ffmpeg_path] + args
        return self.run_process(cmd, timeout_sec=timeout)
