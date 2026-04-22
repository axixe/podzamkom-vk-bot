import tempfile
import unittest
import sqlite3
from pathlib import Path

from infrastructure.db.migrator import DatabaseMigrator
from infrastructure.repositories.sqlite_user_draft_repository import SqliteUserDraftRepository


class SqliteUserDraftRepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        db_path = Path(self._tmp.name) / "app.db"
        migrator = DatabaseMigrator(
            db_path=db_path,
            migrations_dir=Path("infrastructure/db/migrations"),
        )
        migrator.migrate()
        self.db_path = db_path
        self.repository = SqliteUserDraftRepository(db_path=db_path)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_clear_by_user_id_returns_deleted_count(self) -> None:
        self.repository.add_photo(user_id=101, file_id="file_1")
        self.repository.add_photo(user_id=101, file_id="file_2")
        self.repository.add_photo(user_id=202, file_id="file_3")

        deleted_count = self.repository.clear_by_user_id(user_id=101)

        self.assertEqual(deleted_count, 2)
        self.assertEqual(self.repository.count_photos_by_user_id(101), 0)
        self.assertEqual(self.repository.count_photos_by_user_id(202), 1)

    def test_submit_draft_moves_rows_to_queue_and_clears_draft(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO employees (username, platform_user_id, is_active, created_at, updated_at)
                VALUES ('alice', 303, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
            )

        self.repository.add_photo(user_id=303, file_id="file_a")
        self.repository.add_photo(user_id=303, file_id="file_b")

        result = self.repository.submit_draft(user_id=303)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.queued_count, 2)
        self.assertGreater(result.employee_id, 0)
        self.assertEqual(self.repository.count_photos_by_user_id(303), 0)

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT employee_id, status, photo_url
                FROM photo_queue
                ORDER BY id ASC
                """
            ).fetchall()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], result.employee_id)
        self.assertEqual(rows[0][1], "pending")
        self.assertEqual(rows[0][2], "file_a")
        self.assertEqual(rows[1][2], "file_b")

    def test_submit_draft_returns_none_for_empty_draft_and_keeps_queue_unchanged(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO employees (username, platform_user_id, is_active, created_at, updated_at)
                VALUES ('bob', 404, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
            )
            before_count = conn.execute("SELECT COUNT(*) FROM photo_queue").fetchone()[0]

        result = self.repository.submit_draft(user_id=404)

        self.assertIsNone(result)
        with sqlite3.connect(self.db_path) as conn:
            after_count = conn.execute("SELECT COUNT(*) FROM photo_queue").fetchone()[0]
        self.assertEqual(before_count, after_count)


if __name__ == "__main__":
    unittest.main()
