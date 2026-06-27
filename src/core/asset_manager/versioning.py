"""
Versioning Module
Ensures assets are written to and loaded from standardized, version-controlled folders.
E.g., storage/assets/characters/john/v1/, storage/assets/characters/john/v2/
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple

class AssetVersioner:
    """Handles directory path mapping and metadata creation for versioned assets."""
    
    def __init__(self, storage_path: str) -> None:
        self.assets_root = Path(storage_path) / "assets"
        self.assets_root.mkdir(parents=True, exist_ok=True)

    def get_version_dir(self, asset_type: str, name: str, version: int) -> Path:
        """
        Calculates and ensures the directory path for a specific version of an asset.
        """
        asset_dir = self.assets_root / asset_type / name.lower() / f"v{version}"
        asset_dir.mkdir(parents=True, exist_ok=True)
        return asset_dir

    def write_asset_metadata(self, asset_type: str, name: str, version: int, metadata: Dict[str, Any]) -> Path:
        """
        Writes a standard metadata.json file within the asset's version directory.
        """
        v_dir = self.get_version_dir(asset_type, name, version)
        meta_file = v_dir / "metadata.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        return meta_file

    def find_latest_version(self, asset_type: str, name: str) -> Tuple[int, Path]:
        """
        Scans folders to discover the latest version of an asset. Returns (version_number, path).
        """
        base_dir = self.assets_root / asset_type / name.lower()
        if not base_dir.exists():
            return 0, base_dir
            
        versions = []
        for p in base_dir.iterdir():
            if p.is_dir() and p.name.startswith("v"):
                try:
                    ver_num = int(p.name[1:])
                    versions.append(ver_num)
                except ValueError:
                    continue
                    
        if not versions:
            return 0, base_dir
            
        latest_ver = max(versions)
        return latest_ver, base_dir / f"v{latest_ver}"
