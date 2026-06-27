"""
OTIO Timeline Exporter Module
Translates shot schedules and frame lengths into EDL interchange timelines.
"""

from typing import List, Dict, Any

class OTIOExporter:
    """Builds and serializes OpenTimelineIO models for video editors like Premiere or Resolve."""
    
    @staticmethod
    def export_timeline(shots: List[Dict[str, Any]], output_filepath: str) -> str:
        """
        Synthesizes an OpenTimelineIO stack, populating clips with matching durations.
        """
        try:
            import opentimelineio as otio
            
            timeline = otio.schema.Timeline(name="AI Production Studio Export")
            track = otio.schema.Track(name="Video Track", kind=otio.schema.TrackKind.Video)
            timeline.tracks.append(track)
            
            for shot in shots:
                duration_frames = int(shot.get("duration_seconds", 3.0) * 24.0)
                clip = otio.schema.Clip(
                    name=shot.get("shot_id", "shot"),
                    media_reference=otio.schema.ExternalReference(
                        target_url=shot.get("render_path", "")
                    ),
                    source_range=otio.opentime.TimeRange(
                        start_time=otio.opentime.RationalTime(0, 24),
                        duration=otio.opentime.RationalTime(duration_frames, 24)
                    )
                )
                track.append(clip)
                
            otio.adapters.write_to_file(timeline, output_filepath)
            return output_filepath
        except ImportError:
            # Simple fallback text write if opentimelineio is not installed
            with open(output_filepath, "w", encoding="utf-8") as f:
                f.write("# Fallback EDL Text representation\n")
                for shot in shots:
                    f.write(f"CLIP {shot.get('shot_id')} DURATION {shot.get('duration_seconds')}s\n")
            return output_filepath
