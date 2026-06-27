"""
Shot Database Component
Manages SQLite storage and retrieval of individual Shot statuses, render outputs, and failures.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ShotModel(BaseModel):
    """Pydantic model representing a shot's tracking state."""
    id: Optional[int] = None
    shot_id: str
    scene_id: str
    status: str = "pending" # pending, generating, done, failed
    asset_versions: Dict[str, Any] = Field(default_factory=dict)
    render_path: str = ""
    validation_result: Dict[str, Any] = Field(default_factory=dict)
    repair_attempts: int = 0
    updated_at: str = ""

class ShotDB:
    """Handles SQLite operations on the shots table."""
    
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Creates the shots table if it does not exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS shots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shot_id TEXT UNIQUE NOT NULL,
                    scene_id TEXT NOT NULL,
                    status TEXT,
                    asset_versions TEXT,
                    render_path TEXT,
                    validation_result TEXT,
                    repair_attempts INTEGER,
                    updated_at TEXT
                )
            """)
            conn.commit()

    def upsert_shot(self, shot: ShotModel) -> ShotModel:
        """Inserts or updates a shot record in the database."""
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO shots (
                    shot_id, scene_id, status, asset_versions, render_path, 
                    validation_result, repair_attempts, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(shot_id) DO UPDATE SET
                    scene_id = excluded.scene_id,
                    status = excluded.status,
                    asset_versions = excluded.asset_versions,
                    render_path = excluded.render_path,
                    validation_result = excluded.validation_result,
                    repair_attempts = excluded.repair_attempts,
                    updated_at = excluded.updated_at
            """, (
                shot.shot_id,
                shot.scene_id,
                shot.status,
                json.dumps(shot.asset_versions),
                shot.render_path,
                json.dumps(shot.validation_result),
                shot.repair_attempts,
                now
            ))
            conn.commit()
            
            # Fetch inserted/updated id
            cursor.execute("SELECT id FROM shots WHERE shot_id = ?", (shot.shot_id,))
            row = cursor.fetchone()
            if row:
                shot.id = row[0]
                shot.updated_at = now
        return shot

    def get_shot(self, shot_id: str) -> Optional[ShotModel]:
        """Retrieves details of a single shot."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM shots WHERE shot_id = ?", (shot_id,))
            row = cursor.fetchone()
            if row:
                return ShotModel(
                    id=row[0],
                    shot_id=row[1],
                    scene_id=row[2],
                    status=row[3] or "pending",
                    asset_versions=json.loads(row[4]) if row[4] else {},
                    render_path=row[5] or "",
                    validation_result=json.loads(row[6]) if row[6] else {},
                    repair_attempts=row[7] or 0,
                    updated_at=row[8] or ""
                )
        return None

    def get_all_shots(self) -> List[ShotModel]:
        """Returns all registered shots, sorted by shot_id."""
        shots = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM shots ORDER BY shot_id ASC")
            for row in cursor.fetchall():
                shots.append(ShotModel(
                    id=row[0],
                    shot_id=row[1],
                    scene_id=row[2],
                    status=row[3] or "pending",
                    asset_versions=json.loads(row[4]) if row[4] else {},
                    render_path=row[5] or "",
                    validation_result=json.loads(row[6]) if row[6] else {},
                    repair_attempts=row[7] or 0,
                    updated_at=row[8] or ""
                ))
        return shots
sqlite3 = sqlite3
json = json
datetime = datetime
List = List
Dict = Dict
Any = Any
Optional = Optional
BaseModel = BaseModel
Field = Field
ShotModel = ShotModel
