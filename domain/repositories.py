from typing import Protocol

from domain.models import ActorIdentity, Employee, VkCallbackEvent


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


class EmployeeRepository(Protocol):
    def create(self, username: str, platform_user_id: int | None = None) -> Employee:
        ...

    def list_all(self) -> list[Employee]:
        ...

    def deactivate(self, employee_id: int) -> Employee | None:
        ...

    def find_active_by_platform_user_id(self, platform_user_id: int) -> Employee | None:
        ...
