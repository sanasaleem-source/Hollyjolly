"""
OpenTimelineIO Export — builds a professional timeline from shot data.
Exports .otio and .edl for import into Premiere, DaVinci Resolve, Final Cut.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class OTIOExporter:
    """Exports shot timeline to OpenTimelineIO and EDL formats."""

    def export_timeline(self, shots: list[dict], output_filepath: str) -> str:
        """
        Build OTIO timeline from shots list and save to output_filepath.
        Falls back to EDL text file if opentimelineio not installed.
        """
        try:
            import opentimelineio as otio

            timeline = otio.schema.Timeline(name="AI Production Studio Export")
            track = otio.schema.Track(name="Video")
            timeline.tracks.append(track)

            for shot in shots:
                fps = shot.get("fps", 24)
                duration = shot.get("duration_seconds", 3.0)
                render_path = shot.get("render_path", "")

                clip = otio.schema.Clip(
                    name=shot.get("shot_id", "shot"),
                    source_range=otio.opentime.TimeRange(
                        start_time=otio.opentime.RationalTime(0, fps),
                        duration=otio.opentime.RationalTime(duration * fps, fps)
                    )
                )

                if render_path:
                    clip.media_reference = otio.schema.ExternalReference(
                        target_url=render_path
                    )

                track.append(clip)

            otio.adapters.write_to_file(timeline, output_filepath)
            logger.info(f"OTIO timeline saved: {output_filepath}")

            # Also export EDL
            edl_path = output_filepath.replace(".otio", ".edl")
            otio.adapters.write_to_file(timeline, edl_path)
            logger.info(f"EDL saved: {edl_path}")

            return output_filepath

        except ImportError:
            logger.warning("opentimelineio not installed — writing basic EDL")
            return self._write_basic_edl(shots, output_filepath)

    def _write_basic_edl(self, shots: list[dict], output_filepath: str) -> str:
        """Write a basic CMX3600 EDL as fallback."""
        edl_path = output_filepath.replace(".otio", ".edl")
        lines = ["TITLE: AI Production Studio\nFCM: NON-DROP FRAME\n"]
        tc = 0
        for i, shot in enumerate(shots, 1):
            duration = int(shot.get("duration_seconds", 3.0) * 24)
            end = tc + duration
            lines.append(
                f"{i:03d}  AX  V  C  "
                f"{self._frames_to_tc(tc)} {self._frames_to_tc(end)} "
                f"{self._frames_to_tc(tc)} {self._frames_to_tc(end)}"
            )
            tc = end
        with open(edl_path, "w") as f:
            f.write("\n".join(lines))
        logger.info(f"Basic EDL written: {edl_path}")
        return edl_path

    def _frames_to_tc(self, frames: int, fps: int = 24) -> str:
        h = frames // (fps * 3600)
        m = (frames % (fps * 3600)) // (fps * 60)
        s = (frames % (fps * 60)) // fps
        f = frames % fps
        return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"
