from dataclasses import dataclass
from pathlib import Path

from infrastructure.config import AppConfig
from infrastructure.db.migrator import DatabaseMigrator
from infrastructure.repositories.in_memory_event_repository import InMemoryEventRepository
from infrastructure.repositories.sqlite_employee_repository import SqliteEmployeeRepository
from interfaces.admin_handler import AdminHandler
from use_cases.employees import (
    CreateEmployeeUseCase,
    DeactivateEmployeeUseCase,
    ListEmployeesUseCase,
)
from use_cases.process_vk_callback import ProcessVkCallbackUseCase


@dataclass(frozen=True)
class AppContainer:
    """Composition root: связывает реализации инфраструктуры и use cases."""

    event_repository: InMemoryEventRepository
    employee_repository: SqliteEmployeeRepository
    process_vk_callback_use_case: ProcessVkCallbackUseCase
    admin_handler: AdminHandler


def build_container(config: AppConfig) -> AppContainer:
    migrations_dir = Path("infrastructure/db/migrations")

    migrator = DatabaseMigrator(db_path=config.db_path, migrations_dir=migrations_dir)
    migrator.migrate()

    event_repository = InMemoryEventRepository()
    employee_repository = SqliteEmployeeRepository(db_path=config.db_path)

    process_vk_callback_use_case = ProcessVkCallbackUseCase(
        event_repository=event_repository,
        employee_repository=employee_repository,
    )

    admin_handler = AdminHandler(
        create_employee_use_case=CreateEmployeeUseCase(employee_repository=employee_repository),
        list_employees_use_case=ListEmployeesUseCase(employee_repository=employee_repository),
        deactivate_employee_use_case=DeactivateEmployeeUseCase(employee_repository=employee_repository),
    )

    return AppContainer(
        event_repository=event_repository,
        employee_repository=employee_repository,
        process_vk_callback_use_case=process_vk_callback_use_case,
        admin_handler=admin_handler,
    )
