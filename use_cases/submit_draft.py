from dataclasses import dataclass

from domain.models import SubmitDraftResult
from domain.repositories import UserDraftRepository
from domain.services import AdminNotificationsService


class DraftIsEmptyError(ValueError):
    """Черновик пользователя пуст, отправлять нечего."""


@dataclass(slots=True)
class SubmitDraftUseCase:
    user_draft_repository: UserDraftRepository
    admin_notifications_service: AdminNotificationsService

    def execute(self, user_id: int) -> SubmitDraftResult:
        result = self.user_draft_repository.submit_draft(user_id=user_id)
        if result is None:
            raise DraftIsEmptyError("draft is empty")

        self.admin_notifications_service.notify_submit_draft(queued_count=result.queued_count)
        return result
