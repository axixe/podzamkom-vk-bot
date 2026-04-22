from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from domain.models import VkCallbackEvent
from domain.repositories import EventRepository


@dataclass(slots=True)
class ProcessVkCallbackUseCase:
    """Бизнес-операция обработки callback-события без зависимости от транспорта."""

    event_repository: EventRepository

    def execute(self, event_type: str, payload: dict[str, Any]) -> str:
        event = VkCallbackEvent(
            event_type=event_type,
            payload=payload,
            received_at=datetime.now(timezone.utc),
        )
        self.event_repository.save(event)

        if event_type == "confirmation":
            return "need_confirmation_code"

        return "ok"
