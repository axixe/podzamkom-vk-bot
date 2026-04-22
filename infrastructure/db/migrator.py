from pathlib import Path
import sqlite3


class DatabaseMigrator:
    """Запускает SQL-миграции и отмечает примененные версии."""

    def __init__(self, db_path: Path, migrations_dir: Path) -> None:
        self._db_path = db_path
        self._migrations_dir = migrations_dir

    def migrate(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self._db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            applied_versions = {
                row[0]
                for row in connection.execute("SELECT version FROM schema_migrations")
            }

            for migration_file in sorted(self._migrations_dir.glob("*.sql")):
                version = migration_file.stem
                if version in applied_versions:
                    continue

                connection.executescript(migration_file.read_text(encoding="utf-8"))
                connection.execute(
                    "INSERT INTO schema_migrations (version) VALUES (?)",
                    (version,),
                )
