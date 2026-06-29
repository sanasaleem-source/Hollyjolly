"""
FFmpeg Export — assembles rendered frames into final video.
Supports MP4, PNG sequence, and lossless export.
"""
import logging
import os
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class FFmpegExporter:
    """Invokes FFmpeg via ProcessManager to encode shot sequences into video."""

    def __init__(self, process_manager, config: dict) -> None:
        self.pm          = process_manager
        self.ffmpeg_path = config.get("ffmpeg_path", "ffmpeg")
        self.fps         = config.get("render_fps", 24)
        self.storage     = Path(config.get("storage_path", "./storage"))

    def assemble_video(self, shot_ids: List[str], output_path: str) -> bool:
        """
        Assemble frames from multiple shots into a single MP4 video.
        Creates a concat list file then calls FFmpeg.
        """
        concat_path = self.storage / "cache" / "concat_list.txt"
        concat_path.parent.mkdir(parents=True, exist_ok=True)

        lines = []
        for shot_id in shot_ids:
            frame_dir = self.storage / "cache" / shot_id
            frames    = sorted(frame_dir.glob("frame_*.png"))
            for frame in frames:
                lines.append(f"file '{frame.resolve()}'")
                lines.append(f"duration {1.0 / self.fps:.6f}")

        if not lines:
            logger.error("No frames found for any shot — cannot assemble video")
            return False

        with open(concat_path, "w") as f:
            f.write("\n".join(lines))

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-f",        "concat",
            "-safe",     "0",
            "-i",        str(concat_path),
            "-c:v",      "libx264",
            "-pix_fmt",  "yuv420p",
            "-crf",      "18",
            output_path
        ]

        result = self.pm.run_process(cmd, timeout_sec=600)
        if result.returncode == 0:
            logger.info(f"Video assembled: {output_path}")
            return True
        else:
            logger.error(f"FFmpeg failed:\n{result.stderr}")
            return False

    def export_png_sequence(self, shot_id: str, output_dir: str) -> bool:
        """Copy a shot's frames into a numbered PNG sequence folder."""
        src  = self.storage / "cache" / shot_id
        dest = Path(output_dir)
        dest.mkdir(parents=True, exist_ok=True)
        frames = sorted(src.glob("frame_*.png"))
        for i, frame in enumerate(frames):
            import shutil
            shutil.copy2(frame, dest / f"frame_{i:04d}.png")
        logger.info(f"PNG sequence exported: {output_dir} ({len(frames)} frames)")
        return True
