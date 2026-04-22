from typing import Protocol

from domain.models import VkCallbackEvent


class EventRepository(Protocol):
    """Абстракция хранилища входящих callback-событий."""

    def save(self, event: VkCallbackEvent) -> None:
        ...
