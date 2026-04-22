import unittest

from domain.models import ActorIdentity
from infrastructure.repositories.in_memory_event_repository import InMemoryEventRepository
from infrastructure.repositories.in_memory_actor_identity_repository import (
    InMemoryActorIdentityRepository,
)
from tests.helpers.in_memory_employee_repository import InMemoryEmployeeRepository
from tests.helpers.in_memory_processed_event_repository import InMemoryProcessedEventRepository
from tests.helpers.in_memory_user_draft_repository import InMemoryUserDraftRepository
from tests.helpers.spy_admin_notifications_service import SpyAdminNotificationsService
from use_cases.clear_draft import ClearDraftUseCase
from use_cases.identity.resolve_actor_identity import ResolveActorIdentityUseCase
from use_cases.process_vk_callback import ProcessVkCallbackUseCase
from use_cases.submit_draft import SubmitDraftUseCase


class ProcessVkCallbackUseCaseTest(unittest.TestCase):
    def test_rejects_photo_upload_for_inactive_employee(self) -> None:
        event_repository = InMemoryEventRepository()
        employee_repository = InMemoryEmployeeRepository()
        user_draft_repository = InMemoryUserDraftRepository()
        processed_event_repository = InMemoryProcessedEventRepository()
        admin_notifications_service = SpyAdminNotificationsService()
        actor_identity_repository = InMemoryActorIdentityRepository(
            actors=[ActorIdentity(actor_id=1, username="inactive", platform_user_id=300)]
        )
        employee = employee_repository.create(username="inactive", platform_user_id=300)
        employee_repository.deactivate(employee.id)

        use_case = ProcessVkCallbackUseCase(
            event_repository=event_repository,
            processed_event_repository=processed_event_repository,
            employee_repository=employee_repository,
            user_draft_repository=user_draft_repository,
            resolve_actor_identity_use_case=ResolveActorIdentityUseCase(
                actor_identity_repository=actor_identity_repository
            ),
            clear_draft_use_case=ClearDraftUseCase(user_draft_repository=user_draft_repository),
            submit_draft_use_case=SubmitDraftUseCase(
                user_draft_repository=user_draft_repository,
                admin_notifications_service=admin_notifications_service,
            ),
        )

        result = use_case.execute(
            event_type="message_new",
            payload={
                "object": {
                    "message": {
                        "from_id": 300,
                        "attachments": [{"type": "photo", "photo": {"owner_id": 1, "id": 2}}],
                    }
                }
            },
        )

        self.assertEqual(result, "employee_not_allowed")
        self.assertEqual(user_draft_repository.count_photos_by_user_id(300), 0)

    def test_saves_photo_file_ids_in_user_draft_and_returns_count(self) -> None:
        event_repository = InMemoryEventRepository()
        employee_repository = InMemoryEmployeeRepository()
        user_draft_repository = InMemoryUserDraftRepository()
        processed_event_repository = InMemoryProcessedEventRepository()
        admin_notifications_service = SpyAdminNotificationsService()
        actor_identity_repository = InMemoryActorIdentityRepository(
            actors=[ActorIdentity(actor_id=10, username="active", platform_user_id=700)]
        )
        employee_repository.create(username="active", platform_user_id=700)

        use_case = ProcessVkCallbackUseCase(
            event_repository=event_repository,
            processed_event_repository=processed_event_repository,
            employee_repository=employee_repository,
            user_draft_repository=user_draft_repository,
            resolve_actor_identity_use_case=ResolveActorIdentityUseCase(
                actor_identity_repository=actor_identity_repository
            ),
            clear_draft_use_case=ClearDraftUseCase(user_draft_repository=user_draft_repository),
            submit_draft_use_case=SubmitDraftUseCase(
                user_draft_repository=user_draft_repository,
                admin_notifications_service=admin_notifications_service,
            ),
        )

        result = use_case.execute(
            event_type="message_new",
            payload={
                "object": {
                    "message": {
                        "from_id": 700,
                        "attachments": [
                            {
                                "type": "photo",
                                "photo": {"owner_id": 5, "id": 10, "access_key": "abc"},
                            },
                            {"type": "photo", "photo": {"file_id": "  file_123  "}},
                        ],
                    }
                }
            },
        )

        self.assertEqual(result, "draft_updated:2")
        self.assertEqual(
            user_draft_repository.drafts[700],
            ["photo5_10_abc", "file_123"],
        )

    def test_clears_draft_by_clear_command_and_returns_deleted_count(self) -> None:
        event_repository = InMemoryEventRepository()
        employee_repository = InMemoryEmployeeRepository()
        user_draft_repository = InMemoryUserDraftRepository()
        processed_event_repository = InMemoryProcessedEventRepository()
        admin_notifications_service = SpyAdminNotificationsService()
        actor_identity_repository = InMemoryActorIdentityRepository(
            actors=[ActorIdentity(actor_id=10, username="active", platform_user_id=700)]
        )
        employee_repository.create(username="active", platform_user_id=700)
        user_draft_repository.add_photo(user_id=700, file_id="file_1")
        user_draft_repository.add_photo(user_id=700, file_id="file_2")

        use_case = ProcessVkCallbackUseCase(
            event_repository=event_repository,
            processed_event_repository=processed_event_repository,
            employee_repository=employee_repository,
            user_draft_repository=user_draft_repository,
            resolve_actor_identity_use_case=ResolveActorIdentityUseCase(
                actor_identity_repository=actor_identity_repository
            ),
            clear_draft_use_case=ClearDraftUseCase(user_draft_repository=user_draft_repository),
            submit_draft_use_case=SubmitDraftUseCase(
                user_draft_repository=user_draft_repository,
                admin_notifications_service=admin_notifications_service,
            ),
        )

        result = use_case.execute(
            event_type="message_new",
            payload={
                "object": {
                    "message": {
                        "from_id": 700,
                        "text": "/clear",
                    }
                }
            },
        )

        self.assertEqual(result, "draft_cleared:2")
        self.assertEqual(user_draft_repository.count_photos_by_user_id(700), 0)

    def test_ignores_duplicate_event_id_and_skips_second_submit_notification(self) -> None:
        event_repository = InMemoryEventRepository()
        employee_repository = InMemoryEmployeeRepository()
        user_draft_repository = InMemoryUserDraftRepository()
        processed_event_repository = InMemoryProcessedEventRepository()
        admin_notifications_service = SpyAdminNotificationsService()
        actor_identity_repository = InMemoryActorIdentityRepository(
            actors=[ActorIdentity(actor_id=10, username="active", platform_user_id=700)]
        )
        employee_repository.create(username="active", platform_user_id=700)
        user_draft_repository.add_photo(user_id=700, file_id="file_1")

        use_case = ProcessVkCallbackUseCase(
            event_repository=event_repository,
            processed_event_repository=processed_event_repository,
            employee_repository=employee_repository,
            user_draft_repository=user_draft_repository,
            resolve_actor_identity_use_case=ResolveActorIdentityUseCase(
                actor_identity_repository=actor_identity_repository
            ),
            clear_draft_use_case=ClearDraftUseCase(user_draft_repository=user_draft_repository),
            submit_draft_use_case=SubmitDraftUseCase(
                user_draft_repository=user_draft_repository,
                admin_notifications_service=admin_notifications_service,
            ),
        )

        payload = {
            "event_id": "evt-1",
            "object": {
                "message": {
                    "from_id": 700,
                    "text": "/submit",
                }
            },
        }
        first_result = use_case.execute(event_type="message_new", payload=payload)
        second_result = use_case.execute(event_type="message_new", payload=payload)

        self.assertEqual(first_result, "draft_submitted:1:700")
        self.assertEqual(second_result, "duplicate_event")
        self.assertEqual(admin_notifications_service.notified_queued_counts, [1])

    def test_returns_main_menu_for_start_command(self) -> None:
        event_repository = InMemoryEventRepository()
        employee_repository = InMemoryEmployeeRepository()
        user_draft_repository = InMemoryUserDraftRepository()
        processed_event_repository = InMemoryProcessedEventRepository()
        admin_notifications_service = SpyAdminNotificationsService()
        actor_identity_repository = InMemoryActorIdentityRepository(
            actors=[ActorIdentity(actor_id=15, username="active", platform_user_id=901)]
        )
        employee_repository.create(username="active", platform_user_id=901)

        use_case = ProcessVkCallbackUseCase(
            event_repository=event_repository,
            processed_event_repository=processed_event_repository,
            employee_repository=employee_repository,
            user_draft_repository=user_draft_repository,
            resolve_actor_identity_use_case=ResolveActorIdentityUseCase(
                actor_identity_repository=actor_identity_repository
            ),
            clear_draft_use_case=ClearDraftUseCase(user_draft_repository=user_draft_repository),
            submit_draft_use_case=SubmitDraftUseCase(
                user_draft_repository=user_draft_repository,
                admin_notifications_service=admin_notifications_service,
            ),
        )

        result = use_case.execute(
            event_type="message_new",
            payload={
                "object": {
                    "message": {
                        "from_id": 901,
                        "text": "Начать",
                    }
                }
            },
        )

        self.assertEqual(result, "show_main_menu")

    def test_returns_admin_menu_for_start_command_by_admin_without_employee_role(self) -> None:
        event_repository = InMemoryEventRepository()
        employee_repository = InMemoryEmployeeRepository()
        user_draft_repository = InMemoryUserDraftRepository()
        processed_event_repository = InMemoryProcessedEventRepository()
        admin_notifications_service = SpyAdminNotificationsService()
        actor_identity_repository = InMemoryActorIdentityRepository(actors=[])

        use_case = ProcessVkCallbackUseCase(
            event_repository=event_repository,
            processed_event_repository=processed_event_repository,
            employee_repository=employee_repository,
            user_draft_repository=user_draft_repository,
            resolve_actor_identity_use_case=ResolveActorIdentityUseCase(
                actor_identity_repository=actor_identity_repository
            ),
            clear_draft_use_case=ClearDraftUseCase(user_draft_repository=user_draft_repository),
            submit_draft_use_case=SubmitDraftUseCase(
                user_draft_repository=user_draft_repository,
                admin_notifications_service=admin_notifications_service,
            ),
            admin_user_ids=(999,),
        )

        result = use_case.execute(
            event_type="message_new",
            payload={
                "object": {
                    "message": {
                        "from_id": 999,
                        "text": "Начать",
                    }
                }
            },
        )

        self.assertEqual(result, "show_main_menu:admin")


if __name__ == "__main__":
    unittest.main()
