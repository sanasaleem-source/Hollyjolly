"""
Frame Collector Module
Collects and audits rendered frame sequences to confirm expected outputs are complete.
"""

from pathlib import Path
from typing import List

class FrameCollector:
    """Monitors and processes render cache folders."""
    
    @staticmethod
    def collect_frames(shot_id: str, storage_path: str) -> List[str]:
        """
        Locates and returns ordered filepaths of all rendered frames for a specific shot.
        """
        cache_dir = Path(storage_path) / "cache" / shot_id
        if not cache_dir.exists():
            return []
            
        frames = []
        for p in cache_dir.iterdir():
            if p.is_file() and p.suffix.lower() == ".png":
                frames.append(str(p))
                
        return sorted(frames)
