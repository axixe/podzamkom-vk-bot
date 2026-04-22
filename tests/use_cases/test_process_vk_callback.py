import unittest

from infrastructure.repositories.in_memory_event_repository import InMemoryEventRepository
from tests.helpers.in_memory_employee_repository import InMemoryEmployeeRepository
from use_cases.process_vk_callback import ProcessVkCallbackUseCase


class ProcessVkCallbackUseCaseTest(unittest.TestCase):
    def test_rejects_photo_upload_for_inactive_employee(self) -> None:
        event_repository = InMemoryEventRepository()
        employee_repository = InMemoryEmployeeRepository()
        employee = employee_repository.create(username="inactive", platform_user_id=300)
        employee_repository.deactivate(employee.id)

        use_case = ProcessVkCallbackUseCase(
            event_repository=event_repository,
            employee_repository=employee_repository,
        )

        result = use_case.execute(
            event_type="message_new",
            payload={
                "object": {
                    "message": {
                        "from_id": 300,
                        "attachments": [{"type": "photo"}],
                    }
                }
            },
        )

        self.assertEqual(result, "employee_not_allowed")


if __name__ == "__main__":
    unittest.main()
