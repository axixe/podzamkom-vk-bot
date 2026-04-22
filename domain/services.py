from typing import Protocol


class AdminNotificationsService(Protocol):
    """Сервис уведомления администраторов о новых элементах очереди."""

    def notify_submit_draft(self, queued_count: int) -> None:
        ...
