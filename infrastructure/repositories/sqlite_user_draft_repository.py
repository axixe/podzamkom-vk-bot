from __future__ import annotations

import sqlite3
from pathlib import Path


class SqliteUserDraftRepository:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def add_photo(self, user_id: int, file_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO user_drafts (user_id, file_id)
                VALUES (?, ?)
                """,
                (user_id, file_id),
            )

    def count_photos_by_user_id(self, user_id: int) -> int:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS total
                FROM user_drafts
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()

        return int(row["total"]) if row is not None else 0
