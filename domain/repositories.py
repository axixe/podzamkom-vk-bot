from typing import Protocol

from domain.models import ActorIdentity, Employee, SubmitDraftResult, VkCallbackEvent


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


class UserDraftRepository(Protocol):
    def add_photo(self, user_id: int, file_id: str) -> None:
        ...

    def count_photos_by_user_id(self, user_id: int) -> int:
        ...

    def clear_by_user_id(self, user_id: int) -> int:
        ...

    def submit_draft(self, user_id: int) -> SubmitDraftResult | None:
        ...
