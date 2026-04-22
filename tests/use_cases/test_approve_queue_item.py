import unittest
from datetime import datetime, timezone

from domain.models import PhotoQueueItemForReview
from tests.helpers.in_memory_user_draft_repository import InMemoryUserDraftRepository
from use_cases.approve_queue_item import ApproveQueueItemUseCase
from use_cases.review_queue_item_errors import QueueItemDecisionError
from use_cases.take_next_pending_for_review import AccessDeniedError


class ApproveQueueItemUseCaseTest(unittest.TestCase):
    def test_approves_in_review_item(self) -> None:
        repository = InMemoryUserDraftRepository()
        repository.seed_queue(
            [
                PhotoQueueItemForReview(
                    id=1,
                    employee_id=7,
                    photo_url="photo_1",
                    status="in_review",
                    review_started_at=datetime.now(timezone.utc),
                    reviewed_at=None,
                )
            ]
        )
        use_case = ApproveQueueItemUseCase(
            user_draft_repository=repository,
            admin_user_ids=(11,),
        )

        result = use_case.execute(admin_user_id=11, queue_item_id=1)

        self.assertEqual(result.status, "approved")
        self.assertIsNotNone(result.reviewed_at)

    def test_raises_business_error_for_repeated_or_invalid_decision(self) -> None:
        repository = InMemoryUserDraftRepository()
        repository.seed_queue(
            [
                PhotoQueueItemForReview(
                    id=1,
                    employee_id=7,
                    photo_url="photo_1",
                    status="approved",
                    review_started_at=datetime.now(timezone.utc),
                    reviewed_at=datetime.now(timezone.utc),
                )
            ]
        )
        use_case = ApproveQueueItemUseCase(
            user_draft_repository=repository,
            admin_user_ids=(11,),
        )

        with self.assertRaises(QueueItemDecisionError):
            use_case.execute(admin_user_id=11, queue_item_id=1)

    def test_denies_non_admin(self) -> None:
        repository = InMemoryUserDraftRepository()
        use_case = ApproveQueueItemUseCase(
            user_draft_repository=repository,
            admin_user_ids=(11,),
        )

        with self.assertRaises(AccessDeniedError):
            use_case.execute(admin_user_id=44, queue_item_id=1)


if __name__ == "__main__":
    unittest.main()
