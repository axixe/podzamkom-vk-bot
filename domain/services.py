from typing import Protocol


class AdminNotificationsService(Protocol):
    """Сервис уведомления администраторов о новых элементах очереди."""

    def notify_submit_draft(self, queued_count: int) -> None:
        ...


class OutgoingMessageService(Protocol):
    """Сервис отправки исходящих сообщений пользователям платформы."""

    def send_message(self, user_id: int, text: str, keyboard: str | None = None) -> None:
        ...
