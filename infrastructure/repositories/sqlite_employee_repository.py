from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from domain.models import Employee


class SqliteEmployeeRepository:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Employee:
        return Employee(
            id=int(row["id"]),
            username=str(row["username"]),
            platform_user_id=(
                int(row["platform_user_id"]) if row["platform_user_id"] is not None else None
            ),
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )

    def create(self, username: str, platform_user_id: int | None = None) -> Employee:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO employees (username, platform_user_id, is_active, created_at, updated_at)
                VALUES (?, ?, 1, ?, ?)
                """,
                (username, platform_user_id, now, now),
            )
            row = conn.execute(
                "SELECT * FROM employees WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()

        assert row is not None
        return self._from_row(row)

    def list_all(self) -> list[Employee]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM employees ORDER BY id ASC"
            ).fetchall()

        return [self._from_row(row) for row in rows]

    def deactivate(self, employee_id: int) -> Employee | None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE employees
                SET is_active = 0,
                    updated_at = ?
                WHERE id = ?
                """,
                (now, employee_id),
            )
            row = conn.execute(
                "SELECT * FROM employees WHERE id = ?",
                (employee_id,),
            ).fetchone()

        if row is None:
            return None

        return self._from_row(row)

    def find_active_by_platform_user_id(self, platform_user_id: int) -> Employee | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM employees
                WHERE platform_user_id = ? AND is_active = 1
                LIMIT 1
                """,
                (platform_user_id,),
            ).fetchone()

        if row is None:
            return None

        return self._from_row(row)
