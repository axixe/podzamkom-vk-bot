import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
