from __future__ import annotations

import sqlite3
from pathlib import Path

from domain.models import SubmitDraftResult


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

    def clear_by_user_id(self, user_id: int) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                DELETE FROM user_drafts
                WHERE user_id = ?
                """,
                (user_id,),
            )

        return int(cursor.rowcount)

    def submit_draft(self, user_id: int) -> SubmitDraftResult | None:
        with self._connect() as conn:
            employee_row = conn.execute(
                """
                SELECT id
                FROM employees
                WHERE platform_user_id = ? AND is_active = 1
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
            if employee_row is None:
                return None

            draft_rows = conn.execute(
                """
                SELECT file_id
                FROM user_drafts
                WHERE user_id = ? AND file_id IS NOT NULL
                ORDER BY id ASC
                """,
                (user_id,),
            ).fetchall()
            if not draft_rows:
                return None

            employee_id = int(employee_row["id"])
            file_ids = [str(row["file_id"]) for row in draft_rows]

            conn.executemany(
                """
                INSERT INTO photo_queue (employee_id, status, photo_url)
                VALUES (?, 'pending', ?)
                """,
                [(employee_id, file_id) for file_id in file_ids],
            )
            conn.execute(
                """
                DELETE FROM user_drafts
                WHERE user_id = ?
                """,
                (user_id,),
            )

        return SubmitDraftResult(queued_count=len(file_ids), employee_id=employee_id)
