import unittest
from datetime import datetime, timezone

from domain.models import PhotoQueueItemForReview
from tests.helpers.in_memory_user_draft_repository import InMemoryUserDraftRepository
from use_cases.take_next_pending_for_review import (
    AccessDeniedError,
    TakeNextPendingForReviewUseCase,
)


class TakeNextPendingForReviewUseCaseTest(unittest.TestCase):
    def test_takes_pending_item_for_admin(self) -> None:
        repository = InMemoryUserDraftRepository()
        repository.seed_queue(
            [
                PhotoQueueItemForReview(
                    id=1,
                    employee_id=7,
                    photo_url="photo_1",
                    status="pending",
                    review_started_at=None,
                ),
                PhotoQueueItemForReview(
                    id=2,
                    employee_id=8,
                    photo_url="photo_2",
                    status="pending",
                    review_started_at=None,
                ),
            ]
        )
        use_case = TakeNextPendingForReviewUseCase(
            user_draft_repository=repository,
            admin_user_ids=(11, 22),
        )

        result = use_case.execute(admin_user_id=11)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.id, 1)
        self.assertEqual(result.status, "in_review")
        self.assertIsInstance(result.review_started_at, datetime)

    def test_returns_none_without_pending(self) -> None:
        repository = InMemoryUserDraftRepository()
        repository.seed_queue(
            [
                PhotoQueueItemForReview(
                    id=1,
                    employee_id=7,
                    photo_url="photo_1",
                    status="in_review",
                    review_started_at=datetime.now(timezone.utc),
                )
            ]
        )
        use_case = TakeNextPendingForReviewUseCase(
            user_draft_repository=repository,
            admin_user_ids=(11,),
        )

        result = use_case.execute(admin_user_id=11)

        self.assertIsNone(result)

    def test_denies_non_admin(self) -> None:
        repository = InMemoryUserDraftRepository()
        use_case = TakeNextPendingForReviewUseCase(
            user_draft_repository=repository,
            admin_user_ids=(11,),
        )

        with self.assertRaises(AccessDeniedError):
            use_case.execute(admin_user_id=44)


if __name__ == "__main__":
    unittest.main()
