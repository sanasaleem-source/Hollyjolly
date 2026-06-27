"""
Asset Manager Engine
Implements the core decision-making loop: Check if exists -> Reuse -> Create new version.
Coordinates image and mesh generators to procure asset files when missing.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from src.core.asset_manager.versioning import AssetVersioner
from src.core.asset_manager.asset_index import AssetIndex

class AssetManager:
    """Consolidated Asset system driving lookup, versioning, and AI image hook triggers."""
    
    def __init__(self, config: dict, image_provider) -> None:
        self.config = config
        self.image_provider = image_provider
        
        # Instantiate dependencies
        storage_path = config.get("storage_path", "./storage")
        self.versioner = AssetVersioner(storage_path)
        
        db_path = str(Path(storage_path) / "database" / "world_state.db")
        self.index = AssetIndex(db_path)

    def resolve_character_asset(self, name: str, description: str, force_new_version: bool = False) -> str:
        """
        Decision-tree workflow to resolve character images or models:
        1. Does character exist? If yes, and not changed, reuse it.
        2. If force_new_version is True (character changed/damaged), generate a new version.
        3. If doesn't exist, trigger AI Generation.
        """
        asset_type = "characters"
        existing = self.index.lookup_asset(name, asset_type)
        
        if existing and not force_new_version:
            # Step 1: Reuse existing asset
            return existing["path"]
            
        # Determine next version number
        next_ver = 1
        if existing:
            next_ver = existing["version"] + 1
            
        # Step 2 & 3: Create version folder & generate asset via Gemini Imagen
        v_dir = self.versioner.get_version_dir(asset_type, name, next_ver)
        image_path = v_dir / "appearance.png"
        
        # Call AI provider to generate the image bytes
        # Prompt includes design descriptions
        full_prompt = f"A character design of {name}. Description: {description}. Transparent background, studio lighting, character concept art."
        image_bytes = self.image_provider.generate(full_prompt, style_ref=None)
        
        # Save image bytes
        with open(image_path, "wb") as f:
            f.write(image_bytes)
            
        # Write metadata
        meta = {
            "name": name,
            "description": description,
            "version": next_ver,
            "asset_type": asset_type
        }
        self.versioner.write_asset_metadata(asset_type, name, next_ver, meta)
        
        # Register in index
        self.index.register_asset(name, asset_type, next_ver, str(image_path), tags=description)
        
        return str(image_path)

    def resolve_object_asset(self, name: str, description: str, force_new_version: bool = False) -> str:
        """
        Decision-tree workflow to resolve physical props / objects.
        """
        asset_type = "objects"
        existing = self.index.lookup_asset(name, asset_type)
        
        if existing and not force_new_version:
            return existing["path"]
            
        next_ver = 1
        if existing:
            next_ver = existing["version"] + 1
            
        v_dir = self.versioner.get_version_dir(asset_type, name, next_ver)
        image_path = v_dir / "prop.png"
        
        full_prompt = f"An object prop asset of {name}. Description: {description}. Isolated on a solid neutral background, 3D render style."
        image_bytes = self.image_provider.generate(full_prompt, style_ref=None)
        
        with open(image_path, "wb") as f:
            f.write(image_bytes)
            
        meta = {
            "name": name,
            "description": description,
            "version": next_ver,
            "asset_type": asset_type
        }
        self.versioner.write_asset_metadata(asset_type, name, next_ver, meta)
        self.index.register_asset(name, asset_type, next_ver, str(image_path), tags=description)
        
        return str(image_path)

    def resolve_environment_asset(self, name: str, description: str) -> str:
        """
        Resolves environmental layouts, skyboxes, and terrain visuals.
        """
        asset_type = "environments"
        existing = self.index.lookup_asset(name, asset_type)
        
        if existing:
            return existing["path"]
            
        v_dir = self.versioner.get_version_dir(asset_type, name, 1)
        image_path = v_dir / "backdrop.png"
        
        full_prompt = f"An cinematic background scenery of {name}. Description: {description}. High resolution environment concept art."
        image_bytes = self.image_provider.generate(full_prompt, style_ref=None)
        
        with open(image_path, "wb") as f:
            f.write(image_bytes)
            
        meta = {
            "name": name,
            "description": description,
            "version": 1,
            "asset_type": asset_type
        }
        self.versioner.write_asset_metadata(asset_type, name, 1, meta)
        self.index.register_asset(name, asset_type, 1, str(image_path), tags=description)
        
        return str(image_path)
Path = Path
Dict = Dict
Any = Any
List = List
Optional = Optional
AssetVersioner = AssetVersioner
AssetIndex = AssetIndex
