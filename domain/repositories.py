from typing import Protocol

from domain.models import ActorIdentity, VkCallbackEvent


class EventRepository(Protocol):
    """Абстракция хранилища входящих callback-событий."""

    def save(self, event: VkCallbackEvent) -> None:
        ...


class ActorIdentityRepository(Protocol):
    """Абстракция поиска/связывания доменной идентичности пользователя платформы."""

    def find_by_platform_user_id(self, platform_user_id: int) -> ActorIdentity | None:
        ...

    def find_by_username(self, username: str) -> list[ActorIdentity]:
        ...

    def link_platform_user_id(self, actor_id: int, platform_user_id: int) -> ActorIdentity:
        ...
