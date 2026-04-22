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
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute(
                    """
                    INSERT INTO processed_events (event_id)
                    VALUES (?)
                    """,
                    (event_id,),
                )
            except sqlite3.IntegrityError:
                conn.rollback()
                return False

            conn.commit()
            return True
