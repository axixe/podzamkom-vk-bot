from __future__ import annotations

import sqlite3
from pathlib import Path

from domain.models import ActorIdentity


class SqliteActorIdentityRepository:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _from_row(row: sqlite3.Row) -> ActorIdentity:
        return ActorIdentity(
            actor_id=int(row["id"]),
            username=str(row["username"]),
            platform_user_id=(
                int(row["platform_user_id"]) if row["platform_user_id"] is not None else None
            ),
        )

    def find_by_platform_user_id(self, platform_user_id: int) -> ActorIdentity | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, username, platform_user_id
                FROM employees
                WHERE platform_user_id = ?
                LIMIT 1
                """,
                (platform_user_id,),
            ).fetchone()

        return self._from_row(row) if row is not None else None

    def find_by_username(self, username: str) -> list[ActorIdentity]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, username, platform_user_id
                FROM employees
                WHERE username = ?
                ORDER BY id ASC
                """,
                (username,),
            ).fetchall()

        return [self._from_row(row) for row in rows]

    def link_platform_user_id(self, actor_id: int, platform_user_id: int) -> ActorIdentity:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE employees
                SET platform_user_id = ?
                WHERE id = ?
                """,
                (platform_user_id, actor_id),
            )
            row = conn.execute(
                """
                SELECT id, username, platform_user_id
                FROM employees
                WHERE id = ?
                LIMIT 1
                """,
                (actor_id,),
            ).fetchone()

        if row is None:
            raise ValueError(f"Actor with id={actor_id} not found")

        return self._from_row(row)
