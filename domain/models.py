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
