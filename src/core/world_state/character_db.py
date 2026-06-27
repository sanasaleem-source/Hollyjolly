"""
Character Database Component
Manages SQLite storage and retrieval of Character records, represented as Pydantic models.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class CharacterModel(BaseModel):
    """Pydantic model representing a character's state."""
    id: Optional[int] = None
    name: str
    appearance: Dict[str, Any] = Field(default_factory=dict)
    clothing: Dict[str, Any] = Field(default_factory=dict)
    injuries: Dict[str, Any] = Field(default_factory=dict)
    relationships: Dict[str, Any] = Field(default_factory=dict)
    history: str = ""
    last_seen_shot_id: str = ""
    updated_at: str = ""

class CharacterDB:
    """Handles direct SQLite operations on the characters table."""
    
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Creates the characters table if it does not exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS characters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    appearance TEXT,
                    clothing TEXT,
                    injuries TEXT,
                    relationships TEXT,
                    history TEXT,
                    last_seen_shot_id TEXT,
                    updated_at TEXT
                )
            """)
            conn.commit()

    def upsert_character(self, char: CharacterModel) -> CharacterModel:
        """Inserts or updates a character record in the database."""
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO characters (
                    name, appearance, clothing, injuries, relationships, 
                    history, last_seen_shot_id, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    appearance = excluded.appearance,
                    clothing = excluded.clothing,
                    injuries = excluded.injuries,
                    relationships = excluded.relationships,
                    history = excluded.history,
                    last_seen_shot_id = excluded.last_seen_shot_id,
                    updated_at = excluded.updated_at
            """, (
                char.name,
                json.dumps(char.appearance),
                json.dumps(char.clothing),
                json.dumps(char.injuries),
                json.dumps(char.relationships),
                char.history,
                char.last_seen_shot_id,
                now
            ))
            conn.commit()
            
            # Fetch inserted/updated id
            cursor.execute("SELECT id FROM characters WHERE name = ?", (char.name,))
            row = cursor.fetchone()
            if row:
                char.id = row[0]
                char.updated_at = now
        return char

    def get_character(self, name: str) -> Optional[CharacterModel]:
        """Retrieves a single character by their unique name."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM characters WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                return CharacterModel(
                    id=row[0],
                    name=row[1],
                    appearance=json.loads(row[2]) if row[2] else {},
                    clothing=json.loads(row[3]) if row[3] else {},
                    injuries=json.loads(row[4]) if row[4] else {},
                    relationships=json.loads(row[5]) if row[5] else {},
                    history=row[6] or "",
                    last_seen_shot_id=row[7] or "",
                    updated_at=row[8] or ""
                )
        return None

    def get_all_characters(self) -> List[CharacterModel]:
        """Returns a list of all character models stored in the database."""
        characters = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM characters")
            for row in cursor.fetchall():
                characters.append(CharacterModel(
                    id=row[0],
                    name=row[1],
                    appearance=json.loads(row[2]) if row[2] else {},
                    clothing=json.loads(row[3]) if row[3] else {},
                    injuries=json.loads(row[4]) if row[4] else {},
                    relationships=json.loads(row[5]) if row[5] else {},
                    history=row[6] or "",
                    last_seen_shot_id=row[7] or "",
                    updated_at=row[8] or ""
                ))
        return characters
