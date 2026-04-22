from domain.models import VkCallbackEvent


class InMemoryEventRepository:
    """Простая инфраструктурная реализация репозитория для разработки/тестов."""

    def __init__(self) -> None:
        self._events: list[VkCallbackEvent] = []

    def save(self, event: VkCallbackEvent) -> None:
        self._events.append(event)

    @property
    def events(self) -> list[VkCallbackEvent]:
        return self._events
