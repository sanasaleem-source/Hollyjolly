"""
World State Manager
The primary interface that binds CharacterDB, ObjectDB, WorldDB, and ShotDB
into a single cohesive transactional database API.
"""

from typing import List, Optional
from pathlib import Path
from src.core.world_state.character_db import CharacterDB, CharacterModel
from src.core.world_state.object_db import ObjectDB, ObjectModel
from src.core.world_state.world_db import WorldDB, WorldEventModel
from src.core.world_state.shot_db import ShotDB, ShotModel

class WorldStateManager:
    """Consolidated state engine coordinating sqlite schemas under one roof."""
    
    def __init__(self, config: dict) -> None:
        """Initializes state managers using the shared sqlite file path."""
        storage_path = Path(config.get("storage_path", "./storage"))
        db_dir = storage_path / "database"
        db_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = str(db_dir / "world_state.db")
        
        # Instantiate localized DB managers
        self.character_db = CharacterDB(self.db_path)
        self.object_db = ObjectDB(self.db_path)
        self.world_db = WorldDB(self.db_path)
        self.shot_db = ShotDB(self.db_path)

    # CHARACTER APIS
    def save_character(self, character: CharacterModel) -> CharacterModel:
        """Saves or updates a character."""
        return self.character_db.upsert_character(character)

    def get_character(self, name: str) -> Optional[CharacterModel]:
        """Fetches a character profile by name."""
        return self.character_db.get_character(name)

    def get_all_characters(self) -> List[CharacterModel]:
        """Lists all registered characters."""
        return self.character_db.get_all_characters()

    # OBJECT APIS
    def save_object(self, obj: ObjectModel) -> ObjectModel:
        """Saves or updates an object state."""
        return self.object_db.upsert_object(obj)

    def get_object(self, name: str) -> Optional[ObjectModel]:
        """Retrieves an object by name."""
        return self.object_db.get_object(name)

    def get_all_objects(self) -> List[ObjectModel]:
        """Lists all physical objects."""
        return self.object_db.get_all_objects()

    # ENVIRONMENT APIS
    def save_world_event(self, event: WorldEventModel) -> WorldEventModel:
        """Saves or updates world event status."""
        return self.world_db.upsert_world_event(event)

    def get_world_event(self, shot_id: str) -> Optional[WorldEventModel]:
        """Retrieves world event status for a shot."""
        return self.world_db.get_world_event(shot_id)

    def get_world_events(self) -> List[WorldEventModel]:
        """Retrieves all historic world state logs."""
        return self.world_db.get_all_world_events()

    # SHOT APIS
    def save_shot(self, shot: ShotModel) -> ShotModel:
        """Saves or updates status for a shot."""
        return self.shot_db.upsert_shot(shot)

    def get_shot(self, shot_id: str) -> Optional[ShotModel]:
        """Gets shot details by ID."""
        return self.shot_db.get_shot(shot_id)

    def get_all_shots(self) -> List[ShotModel]:
        """Returns all shots in sequence."""
        return self.shot_db.get_all_shots()
