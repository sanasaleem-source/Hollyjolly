"""
Process Manager — spawns and monitors external tool subprocesses.
Never uses check=True — callers inspect returncode themselves.
Never spawns more than one heavy process at a time (V1).
"""
import subprocess
import logging
from typing import List

logger = logging.getLogger(__name__)


class ProcessManager:
    """Manages subprocess spawning for Godot, Blender, and FFmpeg."""

    def __init__(self, config: dict) -> None:
        self.godot_path   = config.get("godot_path",   "godot")
        self.blender_path = config.get("blender_path", "blender")
        self.ffmpeg_path  = config.get("ffmpeg_path",  "ffmpeg")

    def run_process(self, cmd: List[str], timeout_sec: int = 300) -> subprocess.CompletedProcess:
        """
        Run a subprocess. NEVER raises on non-zero exit — callers check returncode.
        Captures stdout and stderr. Enforces timeout.
        """
        logger.info(f"Spawning: {' '.join(str(c) for c in cmd)}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec
                # no check=True — callers handle returncode
            )
            if result.stdout:
                logger.debug(f"stdout: {result.stdout[:500]}")
            if result.stderr and result.returncode != 0:
                logger.warning(f"stderr: {result.stderr[:500]}")
            return result
        except subprocess.TimeoutExpired:
            logger.error(f"Process timed out after {timeout_sec}s: {cmd[0]}")
            # Return a fake CompletedProcess with failure code
            return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="timeout")
        except FileNotFoundError:
            logger.error(f"Executable not found: {cmd[0]} — check config.yaml paths")
            return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="not_found")
        except Exception as e:
            logger.error(f"Unexpected process error: {e}")
            return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr=str(e))
