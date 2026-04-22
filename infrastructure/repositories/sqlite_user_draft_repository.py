from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from domain.models import PhotoQueueItemForReview, SubmitDraftResult


class SqliteUserDraftRepository:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _to_queue_item(row: sqlite3.Row) -> PhotoQueueItemForReview:
        started_at = row["review_started_at"]
        reviewed_at = row["reviewed_at"]
        return PhotoQueueItemForReview(
            id=int(row["id"]),
            employee_id=int(row["employee_id"]),
            photo_url=str(row["photo_url"]) if row["photo_url"] is not None else None,
            status=str(row["status"]),
            review_started_at=datetime.fromisoformat(str(started_at)) if started_at else None,
            reviewed_at=datetime.fromisoformat(str(reviewed_at)) if reviewed_at else None,
        )

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

    def take_next_pending_for_review(self) -> PhotoQueueItemForReview | None:
        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                """
                SELECT id
                FROM photo_queue
                WHERE status = 'pending'
                ORDER BY id ASC
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                conn.commit()
                return None

            queue_id = int(row["id"])
            cursor = conn.execute(
                """
                UPDATE photo_queue
                SET status = 'in_review',
                    review_started_at = ?
                WHERE id = ? AND status = 'pending'
                """,
                (now, queue_id),
            )
            if cursor.rowcount == 0:
                conn.commit()
                return None

            updated = conn.execute(
                """
                SELECT id, employee_id, photo_url, status, review_started_at, reviewed_at
                FROM photo_queue
                WHERE id = ?
                LIMIT 1
                """,
                (queue_id,),
            ).fetchone()
            conn.commit()

        return self._to_queue_item(updated) if updated is not None else None

    def approve_queue_item(self, queue_item_id: int) -> PhotoQueueItemForReview | None:
        return self._resolve_queue_item(queue_item_id=queue_item_id, decision_status="approved")

    def reject_queue_item(self, queue_item_id: int) -> PhotoQueueItemForReview | None:
        return self._resolve_queue_item(queue_item_id=queue_item_id, decision_status="rejected")

    def _resolve_queue_item(
        self,
        queue_item_id: int,
        decision_status: str,
    ) -> PhotoQueueItemForReview | None:
        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.execute(
                """
                UPDATE photo_queue
                SET status = ?,
                    reviewed_at = ?
                WHERE id = ? AND status = 'in_review'
                """,
                (decision_status, now, queue_item_id),
            )
            if cursor.rowcount == 0:
                conn.commit()
                return None

            updated = conn.execute(
                """
                SELECT id, employee_id, photo_url, status, review_started_at, reviewed_at
                FROM photo_queue
                WHERE id = ?
                LIMIT 1
                """,
                (queue_item_id,),
            ).fetchone()
            conn.commit()

        return self._to_queue_item(updated) if updated is not None else None
