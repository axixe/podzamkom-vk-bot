from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class VkCallbackEvent:
    """Входное событие VK callback API в терминах домена."""

    event_type: str
    payload: dict[str, Any]
    received_at: datetime
