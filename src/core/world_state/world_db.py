"""
World events Database Component
Manages SQLite storage and retrieval of World Settings and events.
"""

import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class WorldEventModel(BaseModel):
    """Pydantic model representing world settings and occurrences per shot."""
    id: Optional[int] = None
    shot_id: str
    time_of_day: str = "Day"
    weather: str = "Clear"
    lighting: str = "Standard"
    damage_state: Dict[str, Any] = Field(default_factory=dict)
    events: Dict[str, Any] = Field(default_factory=dict)
    updated_at: str = ""

class WorldDB:
    """Handles SQLite operations on the world_events table."""
    
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Creates the world_events table if it does not exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS world_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shot_id TEXT UNIQUE NOT NULL,
                    time_of_day TEXT,
                    weather TEXT,
                    lighting TEXT,
                    damage_state TEXT,
                    events TEXT,
                    updated_at TEXT
                )
            """)
            conn.commit()

    def upsert_world_event(self, event: WorldEventModel) -> WorldEventModel:
        """Inserts or updates a world setting record in the database."""
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO world_events (
                    shot_id, time_of_day, weather, lighting, damage_state, 
                    events, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(shot_id) DO UPDATE SET
                    time_of_day = excluded.time_of_day,
                    weather = excluded.weather,
                    lighting = excluded.lighting,
                    damage_state = excluded.damage_state,
                    events = excluded.events,
                    updated_at = excluded.updated_at
            """, (
                event.shot_id,
                event.time_of_day,
                event.weather,
                event.lighting,
                json.dumps(event.damage_state),
                json.dumps(event.events),
                now
            ))
            conn.commit()
            
            # Fetch inserted/updated id
            cursor.execute("SELECT id FROM world_events WHERE shot_id = ?", (event.shot_id,))
            row = cursor.fetchone()
            if row:
                event.id = row[0]
                event.updated_at = now
        return event

    def get_world_event(self, shot_id: str) -> Optional[WorldEventModel]:
        """Retrieves world environmental status for a specific shot."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM world_events WHERE shot_id = ?", (shot_id,))
            row = cursor.fetchone()
            if row:
                return WorldEventModel(
                    id=row[0],
                    shot_id=row[1],
                    time_of_day=row[2] or "Day",
                    weather=row[3] or "Clear",
                    lighting=row[4] or "Standard",
                    damage_state=json.loads(row[5]) if row[5] else {},
                    events=json.loads(row[6]) if row[6] else {},
                    updated_at=row[7] or ""
                )
        return None

    def get_all_world_events(self) -> List[WorldEventModel]:
        """Returns all historic world events."""
        events = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM world_events")
            for row in cursor.fetchall():
                events.append(WorldEventModel(
                    id=row[0],
                    shot_id=row[1],
                    time_of_day=row[2] or "Day",
                    weather=row[3] or "Clear",
                    lighting=row[4] or "Standard",
                    damage_state=json.loads(row[5]) if row[5] else {},
                    events=json.loads(row[6]) if row[6] else {},
                    updated_at=row[7] or ""
                ))
        return events
