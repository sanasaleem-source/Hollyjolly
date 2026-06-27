"""
Asset Index Module
Maintains an in-memory and SQLite-backed registry of all versioned assets for instant lookup.
"""

import sqlite3
from typing import Dict, Any, List, Optional

class AssetIndex:
    """Provides fast lookup of assets based on characteristics or identifiers."""
    
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initializes the asset lookup index table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS asset_index (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    asset_type TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    path TEXT UNIQUE NOT NULL,
                    tags TEXT,
                    UNIQUE(name, asset_type, version)
                )
            """)
            conn.commit()

    def register_asset(self, name: str, asset_type: str, version: int, path: str, tags: str = "") -> None:
        """Registers an asset version in the database lookup index."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO asset_index (name, asset_type, version, path, tags)
                VALUES (?, ?, ?, ?, ?)
            """, (name.lower(), asset_type, version, path, tags))
            conn.commit()

    def lookup_asset(self, name: str, asset_type: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves the exact disk path and meta information for an asset.
        If version is omitted, returns the latest registered version.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if version is not None:
                cursor.execute("""
                    SELECT name, asset_type, version, path, tags FROM asset_index 
                    WHERE name = ? AND asset_type = ? AND version = ?
                """, (name.lower(), asset_type, version))
            else:
                cursor.execute("""
                    SELECT name, asset_type, version, path, tags FROM asset_index 
                    WHERE name = ? AND asset_type = ? 
                    ORDER BY version DESC LIMIT 1
                """, (name.lower(), asset_type))
                
            row = cursor.fetchone()
            if row:
                return {
                    "name": row[0],
                    "asset_type": row[1],
                    "version": row[2],
                    "path": row[3],
                    "tags": row[4] or ""
                }
        return None

    def list_all_assets(self) -> List[Dict[str, Any]]:
        """Returns all entries registered in the asset index."""
        assets = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, asset_type, version, path, tags FROM asset_index")
            for row in cursor.fetchall():
                assets.append({
                    "name": row[0],
                    "asset_type": row[1],
                    "version": row[2],
                    "path": row[3],
                    "tags": row[4] or ""
                })
        return assets
sqlite3 = sqlite3
Dict = Dict
Any = Any
List = List
Optional = Optional
