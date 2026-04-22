import unittest

from tests.helpers.in_memory_user_draft_repository import InMemoryUserDraftRepository
from tests.helpers.spy_admin_notifications_service import SpyAdminNotificationsService
from use_cases.submit_draft import DraftIsEmptyError, SubmitDraftUseCase


class SubmitDraftUseCaseTest(unittest.TestCase):
    def test_returns_queued_count_and_employee_id(self) -> None:
        repository = InMemoryUserDraftRepository()
        notifications = SpyAdminNotificationsService()
        repository.add_photo(user_id=501, file_id="one")
        repository.add_photo(user_id=501, file_id="two")
        use_case = SubmitDraftUseCase(
            user_draft_repository=repository,
            admin_notifications_service=notifications,
        )

        result = use_case.execute(user_id=501)

        self.assertEqual(result.queued_count, 2)
        self.assertEqual(result.employee_id, 501)
        self.assertEqual(repository.count_photos_by_user_id(501), 0)
        self.assertEqual(notifications.notified_queued_counts, [2])

    def test_raises_business_error_for_empty_draft(self) -> None:
        notifications = SpyAdminNotificationsService()
        use_case = SubmitDraftUseCase(
            user_draft_repository=InMemoryUserDraftRepository(),
            admin_notifications_service=notifications,
        )

        with self.assertRaises(DraftIsEmptyError):
            use_case.execute(user_id=502)
        self.assertEqual(notifications.notified_queued_counts, [])


if __name__ == "__main__":
    unittest.main()
