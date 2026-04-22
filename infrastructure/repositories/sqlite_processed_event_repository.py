from __future__ import annotations

import sqlite3
from pathlib import Path


class SqliteProcessedEventRepository:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def mark_processed_if_new(self, event_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO processed_events (event_id)
                VALUES (?)
                """,
                (event_id,),
            )

        return int(cursor.rowcount) > 0
