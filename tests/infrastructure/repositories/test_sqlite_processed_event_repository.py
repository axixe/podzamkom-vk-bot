import tempfile
import unittest
from pathlib import Path

from infrastructure.db.migrator import DatabaseMigrator
from infrastructure.repositories.sqlite_processed_event_repository import (
    SqliteProcessedEventRepository,
)


class SqliteProcessedEventRepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        db_path = Path(self._tmp.name) / "app.db"
        migrator = DatabaseMigrator(
            db_path=db_path,
            migrations_dir=Path("infrastructure/db/migrations"),
        )
        migrator.migrate()
        self.repository = SqliteProcessedEventRepository(db_path=db_path)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_returns_false_on_primary_key_conflict(self) -> None:
        first = self.repository.mark_processed_if_new("evt-1")
        second = self.repository.mark_processed_if_new("evt-1")

        self.assertTrue(first)
        self.assertFalse(second)


if __name__ == "__main__":
    unittest.main()
