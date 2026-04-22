import unittest

from domain.models import ActorIdentity
from infrastructure.repositories.in_memory_event_repository import InMemoryEventRepository
from infrastructure.repositories.in_memory_actor_identity_repository import (
    InMemoryActorIdentityRepository,
)
from tests.helpers.in_memory_employee_repository import InMemoryEmployeeRepository
from tests.helpers.in_memory_user_draft_repository import InMemoryUserDraftRepository
from use_cases.identity.resolve_actor_identity import ResolveActorIdentityUseCase
from use_cases.process_vk_callback import ProcessVkCallbackUseCase


class ProcessVkCallbackUseCaseTest(unittest.TestCase):
    def test_rejects_photo_upload_for_inactive_employee(self) -> None:
        event_repository = InMemoryEventRepository()
        employee_repository = InMemoryEmployeeRepository()
        user_draft_repository = InMemoryUserDraftRepository()
        actor_identity_repository = InMemoryActorIdentityRepository(
            actors=[ActorIdentity(actor_id=1, username="inactive", platform_user_id=300)]
        )
        employee = employee_repository.create(username="inactive", platform_user_id=300)
        employee_repository.deactivate(employee.id)

        use_case = ProcessVkCallbackUseCase(
            event_repository=event_repository,
            employee_repository=employee_repository,
            user_draft_repository=user_draft_repository,
            resolve_actor_identity_use_case=ResolveActorIdentityUseCase(
                actor_identity_repository=actor_identity_repository
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
        actor_identity_repository = InMemoryActorIdentityRepository(
            actors=[ActorIdentity(actor_id=10, username="active", platform_user_id=700)]
        )
        employee_repository.create(username="active", platform_user_id=700)

        use_case = ProcessVkCallbackUseCase(
            event_repository=event_repository,
            employee_repository=employee_repository,
            user_draft_repository=user_draft_repository,
            resolve_actor_identity_use_case=ResolveActorIdentityUseCase(
                actor_identity_repository=actor_identity_repository
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


if __name__ == "__main__":
    unittest.main()
