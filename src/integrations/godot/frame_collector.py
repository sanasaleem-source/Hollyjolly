"""
Frame Collector — validates and collects rendered PNG frames from Godot output directory.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FrameCollector:
    """Collects and validates rendered frames from a Godot output directory."""

    def collect(self, output_dir: str) -> list[str]:
        """
        Scan output_dir for frame_XXXX.png files in order.
        Returns sorted list of absolute frame paths.
        """
        path = Path(output_dir)
        if not path.exists():
            logger.error(f"Frame output directory does not exist: {output_dir}")
            return []

        frames = sorted(path.glob("frame_*.png"))
        if not frames:
            logger.warning(f"No frames found in {output_dir}")
            return []

        paths = [str(f.resolve()) for f in frames]
        logger.info(f"Collected {len(paths)} frames from {output_dir}")
        return paths

    def validate(self, frame_paths: list[str]) -> bool:
        """Check all expected frames exist and are non-zero size."""
        for fp in frame_paths:
            p = Path(fp)
            if not p.exists() or p.stat().st_size == 0:
                logger.error(f"Invalid frame: {fp}")
                return False
        return True
