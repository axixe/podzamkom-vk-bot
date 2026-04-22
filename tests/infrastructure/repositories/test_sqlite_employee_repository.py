import tempfile
import unittest
from pathlib import Path

from infrastructure.db.migrator import DatabaseMigrator
from infrastructure.repositories.sqlite_employee_repository import SqliteEmployeeRepository


class SqliteEmployeeRepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        db_path = Path(self._tmp.name) / "app.db"
        migrator = DatabaseMigrator(
            db_path=db_path,
            migrations_dir=Path("infrastructure/db/migrations"),
        )
        migrator.migrate()
        self.repository = SqliteEmployeeRepository(db_path=db_path)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_create_with_existing_platform_user_id_returns_existing_active_employee(self) -> None:
        created = self.repository.create(username="alice", platform_user_id=42)

        updated = self.repository.create(username="alice_new", platform_user_id=42)

        self.assertEqual(updated.id, created.id)
        self.assertEqual(updated.username, "alice_new")
        self.assertTrue(updated.is_active)

    def test_create_reactivates_deactivated_employee(self) -> None:
        created = self.repository.create(username="bob", platform_user_id=77)
        deactivated = self.repository.deactivate(created.id)
        self.assertIsNotNone(deactivated)

        reactivated = self.repository.create(username="bob_returned", platform_user_id=77)

        self.assertEqual(reactivated.id, created.id)
        self.assertTrue(reactivated.is_active)
        self.assertEqual(reactivated.username, "bob_returned")


if __name__ == "__main__":
    unittest.main()
