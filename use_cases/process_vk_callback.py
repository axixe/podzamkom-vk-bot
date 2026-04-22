from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from domain.models import VkCallbackEvent
from domain.repositories import EmployeeRepository, EventRepository


@dataclass(slots=True)
class ProcessVkCallbackUseCase:
    """Бизнес-операция обработки callback-события без зависимости от транспорта."""

    event_repository: EventRepository
    employee_repository: EmployeeRepository

    def execute(self, event_type: str, payload: dict[str, Any]) -> str:
        event = VkCallbackEvent(
            event_type=event_type,
            payload=payload,
            received_at=datetime.now(timezone.utc),
        )
        self.event_repository.save(event)

        if event_type == "confirmation":
            return "need_confirmation_code"

        if event_type == "message_new" and self._has_photo_attachment(payload):
            from_id = self._extract_from_id(payload)
            if from_id is None:
                return "employee_not_allowed"

            employee = self.employee_repository.find_active_by_platform_user_id(from_id)
            if employee is None:
                return "employee_not_allowed"

            return "photo_upload_allowed"

        return "ok"

    @staticmethod
    def _extract_from_id(payload: dict[str, Any]) -> int | None:
        event_object = payload.get("object")
        if not isinstance(event_object, dict):
            return None

        message = event_object.get("message")
        if isinstance(message, dict) and isinstance(message.get("from_id"), int):
            return int(message["from_id"])

        if isinstance(event_object.get("from_id"), int):
            return int(event_object["from_id"])

        return None

    @staticmethod
    def _has_photo_attachment(payload: dict[str, Any]) -> bool:
        event_object = payload.get("object")
        if not isinstance(event_object, dict):
            return False

        message = event_object.get("message") if isinstance(event_object.get("message"), dict) else event_object
        attachments = message.get("attachments") if isinstance(message, dict) else None

        if not isinstance(attachments, list):
            return False

        for attachment in attachments:
            if isinstance(attachment, dict) and attachment.get("type") == "photo":
                return True

        return False
