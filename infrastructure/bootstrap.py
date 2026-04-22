from dataclasses import dataclass
from pathlib import Path

from infrastructure.config import AppConfig
from infrastructure.db.migrator import DatabaseMigrator
from infrastructure.repositories.in_memory_event_repository import InMemoryEventRepository
from infrastructure.repositories.sqlite_actor_identity_repository import SqliteActorIdentityRepository
from infrastructure.repositories.sqlite_employee_repository import SqliteEmployeeRepository
from infrastructure.repositories.sqlite_user_draft_repository import SqliteUserDraftRepository
from interfaces.admin_handler import AdminHandler
from use_cases.clear_draft import ClearDraftUseCase
from use_cases.employees import (
    CreateEmployeeUseCase,
    DeactivateEmployeeUseCase,
    ListEmployeesUseCase,
)
from use_cases.identity.resolve_actor_identity import ResolveActorIdentityUseCase
from use_cases.approve_queue_item import ApproveQueueItemUseCase
from use_cases.process_vk_callback import ProcessVkCallbackUseCase
from use_cases.reject_queue_item import RejectQueueItemUseCase
from use_cases.submit_draft import SubmitDraftUseCase
from use_cases.take_next_pending_for_review import TakeNextPendingForReviewUseCase


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
    actor_identity_repository = SqliteActorIdentityRepository(db_path=config.db_path)
    user_draft_repository = SqliteUserDraftRepository(db_path=config.db_path)
    resolve_actor_identity_use_case = ResolveActorIdentityUseCase(
        actor_identity_repository=actor_identity_repository
    )

    process_vk_callback_use_case = ProcessVkCallbackUseCase(
        event_repository=event_repository,
        employee_repository=employee_repository,
        user_draft_repository=user_draft_repository,
        resolve_actor_identity_use_case=resolve_actor_identity_use_case,
        clear_draft_use_case=ClearDraftUseCase(user_draft_repository=user_draft_repository),
        submit_draft_use_case=SubmitDraftUseCase(user_draft_repository=user_draft_repository),
    )

    admin_handler = AdminHandler(
        create_employee_use_case=CreateEmployeeUseCase(employee_repository=employee_repository),
        list_employees_use_case=ListEmployeesUseCase(employee_repository=employee_repository),
        deactivate_employee_use_case=DeactivateEmployeeUseCase(employee_repository=employee_repository),
        take_next_pending_for_review_use_case=TakeNextPendingForReviewUseCase(
            user_draft_repository=user_draft_repository,
            admin_user_ids=config.admin_user_ids,
        ),
        approve_queue_item_use_case=ApproveQueueItemUseCase(
            user_draft_repository=user_draft_repository,
            admin_user_ids=config.admin_user_ids,
        ),
        reject_queue_item_use_case=RejectQueueItemUseCase(
            user_draft_repository=user_draft_repository,
            admin_user_ids=config.admin_user_ids,
        ),
    )

    return AppContainer(
        event_repository=event_repository,
        employee_repository=employee_repository,
        process_vk_callback_use_case=process_vk_callback_use_case,
        admin_handler=admin_handler,
    )
