"""
World State Manager — unified API over all four DB classes.
Accepts config dict. Creates database directory automatically.
"""
import logging
from pathlib import Path
from typing import List, Optional

from src.core.world_state.character_db import CharacterDB, CharacterModel
from src.core.world_state.object_db import ObjectDB, ObjectModel
from src.core.world_state.world_db import WorldDB, WorldEventModel
from src.core.world_state.shot_db import ShotDB, ShotModel

logger = logging.getLogger(__name__)


class WorldStateManager:
    """Consolidated state engine. Every pipeline system reads/writes through here."""

    def __init__(self, config: dict) -> None:
        storage_path = Path(config.get("storage_path", "./storage"))
        db_dir = storage_path / "database"
        db_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = str(db_dir / "world_state.db")

        self.character_db = CharacterDB(self.db_path)
        self.object_db    = ObjectDB(self.db_path)
        self.world_db     = WorldDB(self.db_path)
        self.shot_db      = ShotDB(self.db_path)
        logger.info(f"WorldStateManager initialised at {self.db_path}")

    # ── Characters ──────────────────────────────────────────────
    def save_character(self, character: CharacterModel) -> CharacterModel:
        return self.character_db.upsert_character(character)

    def get_character(self, name: str) -> Optional[CharacterModel]:
        return self.character_db.get_character(name)

    def get_all_characters(self) -> List[CharacterModel]:
        return self.character_db.get_all_characters()

    # ── Objects ─────────────────────────────────────────────────
    def save_object(self, obj: ObjectModel) -> ObjectModel:
        return self.object_db.upsert_object(obj)

    def get_object(self, name: str) -> Optional[ObjectModel]:
        return self.object_db.get_object(name)

    def get_all_objects(self) -> List[ObjectModel]:
        return self.object_db.get_all_objects()

    # ── World events ────────────────────────────────────────────
    def save_world_event(self, event: WorldEventModel) -> WorldEventModel:
        return self.world_db.upsert_world_event(event)

    def get_world_event(self, shot_id: str) -> Optional[WorldEventModel]:
        return self.world_db.get_world_event(shot_id)

    def get_world_events(self) -> List[WorldEventModel]:
        return self.world_db.get_all_world_events()

    # ── Shots ───────────────────────────────────────────────────
    def save_shot(self, shot: ShotModel) -> ShotModel:
        return self.shot_db.upsert_shot(shot)

    def get_shot(self, shot_id: str) -> Optional[ShotModel]:
        return self.shot_db.get_shot(shot_id)

    def get_all_shots(self) -> List[ShotModel]:
        return self.shot_db.get_all_shots()

    def get_shot_history(self) -> list:
        """Return shots as plain dicts for use in validator prompts."""
        shots = self.shot_db.get_all_shots()
        return [s.model_dump() for s in shots]

    def get_style_reference(self) -> str:
        """Return style reference string from first completed shot, or empty."""
        shots = self.shot_db.get_all_shots()
        for s in shots:
            if s.status == "done" and s.validation_result:
                style = s.validation_result.get("style_reference", "")
                if style:
                    return style
        return "cinematic, consistent color grading, film grain"
