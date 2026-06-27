"""
Object Database Component
Manages SQLite storage and retrieval of Object/Prop records.
"""

import sqlite3
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class ObjectModel(BaseModel):
    """Pydantic model representing an object's state and location."""
    id: Optional[int] = None
    name: str
    owner: str = ""
    condition: str = "Good"
    location: str = ""
    version: int = 1
    updated_at: str = ""

class ObjectDB:
    """Handles SQLite operations on the objects table."""
    
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Creates the objects table if it does not exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS objects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    owner TEXT,
                    condition TEXT,
                    location TEXT,
                    version INTEGER,
                    updated_at TEXT
                )
            """)
            conn.commit()

    def upsert_object(self, obj: ObjectModel) -> ObjectModel:
        """Inserts or updates an object state record in the database."""
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO objects (
                    name, owner, condition, location, version, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    owner = excluded.owner,
                    condition = excluded.condition,
                    location = excluded.location,
                    version = excluded.version,
                    updated_at = excluded.updated_at
            """, (
                obj.name,
                obj.owner,
                obj.condition,
                obj.location,
                obj.version,
                now
            ))
            conn.commit()
            
            # Fetch inserted/updated id
            cursor.execute("SELECT id FROM objects WHERE name = ?", (obj.name,))
            row = cursor.fetchone()
            if row:
                obj.id = row[0]
                obj.updated_at = now
        return obj

    def get_object(self, name: str) -> Optional[ObjectModel]:
        """Retrieves a single object by name."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM objects WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                return ObjectModel(
                    id=row[0],
                    name=row[1],
                    owner=row[2] or "",
                    condition=row[3] or "Good",
                    location=row[4] or "",
                    version=row[5] or 1,
                    updated_at=row[6] or ""
                )
        return None

    def get_all_objects(self) -> List[ObjectModel]:
        """Returns all objects stored in the database."""
        objects = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM objects")
            for row in cursor.fetchall():
                objects.append(ObjectModel(
                    id=row[0],
                    name=row[1],
                    owner=row[2] or "",
                    condition=row[3] or "Good",
                    location=row[4] or "",
                    version=row[5] or 1,
                    updated_at=row[6] or ""
                ))
        return objects
sqlite3 = sqlite3
datetime = datetime
List = List
Optional = Optional
BaseModel = BaseModel
ObjectModel = ObjectModel
