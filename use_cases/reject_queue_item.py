from dataclasses import dataclass

from domain.models import PhotoQueueItemForReview
from domain.repositories import UserDraftRepository
from use_cases.review_queue_item_errors import QueueItemDecisionError
from use_cases.take_next_pending_for_review import AccessDeniedError


@dataclass(slots=True)
class RejectQueueItemUseCase:
    user_draft_repository: UserDraftRepository
    admin_user_ids: tuple[int, ...]

    def execute(self, admin_user_id: int, queue_item_id: int) -> PhotoQueueItemForReview:
        if admin_user_id not in self.admin_user_ids:
            raise AccessDeniedError("admin access required")

        item = self.user_draft_repository.reject_queue_item(queue_item_id=queue_item_id)
        if item is None:
            raise QueueItemDecisionError("queue item cannot be rejected")

        return item
