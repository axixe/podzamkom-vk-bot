from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class VkCallbackEvent:
    """Входное событие VK callback API в терминах домена."""

    event_type: str
    payload: dict[str, Any]
    received_at: datetime


@dataclass(frozen=True)
class ActorIdentity:
    """Доменная проекция участника системы для идентификации по VK данным."""

    actor_id: int
    username: str
    platform_user_id: int | None


@dataclass(frozen=True)
class Employee:
    """Сотрудник, связанный с VK user и статусом активности."""

    id: int
    username: str
    platform_user_id: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class SubmitDraftResult:
    """Результат отправки черновика в очередь обработки."""

    queued_count: int
    employee_id: int


@dataclass(frozen=True)
class PhotoQueueItemForReview:
    """Элемент очереди фото, взятый в модерацию."""

    id: int
    employee_id: int
    photo_url: str | None
    status: str
    review_started_at: datetime | None
    reviewed_at: datetime | None
