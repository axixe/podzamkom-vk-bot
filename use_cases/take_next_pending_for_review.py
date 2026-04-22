from dataclasses import dataclass

from domain.models import PhotoQueueItemForReview
from domain.repositories import UserDraftRepository


class AccessDeniedError(PermissionError):
    """Операция доступна только администраторам."""


@dataclass(slots=True)
class TakeNextPendingForReviewUseCase:
    user_draft_repository: UserDraftRepository
    admin_user_ids: tuple[int, ...]

    def execute(self, admin_user_id: int) -> PhotoQueueItemForReview | None:
        if admin_user_id not in self.admin_user_ids:
            raise AccessDeniedError("admin access required")

        return self.user_draft_repository.take_next_pending_for_review()
