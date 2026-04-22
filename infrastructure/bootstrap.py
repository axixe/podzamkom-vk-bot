from dataclasses import dataclass
from pathlib import Path

from infrastructure.config import AppConfig
from infrastructure.db.migrator import DatabaseMigrator
from infrastructure.repositories.in_memory_event_repository import InMemoryEventRepository
from use_cases.process_vk_callback import ProcessVkCallbackUseCase


@dataclass(frozen=True)
class AppContainer:
    """Composition root: связывает реализации инфраструктуры и use cases."""

    event_repository: InMemoryEventRepository
    process_vk_callback_use_case: ProcessVkCallbackUseCase


def build_container(config: AppConfig) -> AppContainer:
    migrations_dir = Path("infrastructure/db/migrations")

    migrator = DatabaseMigrator(db_path=config.db_path, migrations_dir=migrations_dir)
    migrator.migrate()

    event_repository = InMemoryEventRepository()
    process_vk_callback_use_case = ProcessVkCallbackUseCase(
        event_repository=event_repository,
    )

    return AppContainer(
        event_repository=event_repository,
        process_vk_callback_use_case=process_vk_callback_use_case,
    )
