from datetime import datetime, timezone

from domain.models import PhotoQueueItemForReview, SubmitDraftResult


class InMemoryUserDraftRepository:
    def __init__(self) -> None:
        self._drafts: dict[int, list[str]] = {}
        self._queue: list[PhotoQueueItemForReview] = []

    def add_photo(self, user_id: int, file_id: str) -> None:
        self._drafts.setdefault(user_id, []).append(file_id)

    def count_photos_by_user_id(self, user_id: int) -> int:
        return len(self._drafts.get(user_id, []))

    def clear_by_user_id(self, user_id: int) -> int:
        deleted = len(self._drafts.get(user_id, []))
        self._drafts.pop(user_id, None)
        return deleted

    def submit_draft(self, user_id: int) -> SubmitDraftResult | None:
        file_ids = self._drafts.get(user_id, [])
        if not file_ids:
            return None

        self._drafts.pop(user_id, None)
        return SubmitDraftResult(queued_count=len(file_ids), employee_id=user_id)

    def take_next_pending_for_review(self) -> PhotoQueueItemForReview | None:
        for index, item in enumerate(self._queue):
            if item.status != "pending":
                continue

            updated = PhotoQueueItemForReview(
                id=item.id,
                employee_id=item.employee_id,
                photo_url=item.photo_url,
                status="in_review",
                review_started_at=datetime.now(timezone.utc),
                reviewed_at=None,
            )
            self._queue[index] = updated
            return updated

        return None

    def approve_queue_item(self, queue_item_id: int) -> PhotoQueueItemForReview | None:
        return self._resolve_queue_item(queue_item_id=queue_item_id, decision_status="approved")

    def reject_queue_item(self, queue_item_id: int) -> PhotoQueueItemForReview | None:
        return self._resolve_queue_item(queue_item_id=queue_item_id, decision_status="rejected")

    def _resolve_queue_item(
        self,
        queue_item_id: int,
        decision_status: str,
    ) -> PhotoQueueItemForReview | None:
        for index, item in enumerate(self._queue):
            if item.id != queue_item_id or item.status != "in_review":
                continue

            updated = PhotoQueueItemForReview(
                id=item.id,
                employee_id=item.employee_id,
                photo_url=item.photo_url,
                status=decision_status,
                review_started_at=item.review_started_at,
                reviewed_at=datetime.now(timezone.utc),
            )
            self._queue[index] = updated
            return updated

        return None

    def seed_queue(self, items: list[PhotoQueueItemForReview]) -> None:
        self._queue = list(items)

    @property
    def drafts(self) -> dict[int, list[str]]:
        return self._drafts
