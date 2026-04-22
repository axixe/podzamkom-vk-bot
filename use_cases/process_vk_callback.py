from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from domain.models import VkCallbackEvent
from domain.repositories import EmployeeRepository, EventRepository, UserDraftRepository
from use_cases.identity.resolve_actor_identity import ResolveActorIdentityUseCase


@dataclass(slots=True)
class ProcessVkCallbackUseCase:
    """Бизнес-операция обработки callback-события без зависимости от транспорта."""

    event_repository: EventRepository
    employee_repository: EmployeeRepository
    user_draft_repository: UserDraftRepository
    resolve_actor_identity_use_case: ResolveActorIdentityUseCase

    def execute(self, event_type: str, payload: dict[str, Any]) -> str:
        event = VkCallbackEvent(
            event_type=event_type,
            payload=payload,
            received_at=datetime.now(timezone.utc),
        )
        self.event_repository.save(event)

        if event_type == "confirmation":
            return "need_confirmation_code"

        if event_type == "message_new":
            from_id = self._extract_from_id(payload)
            if from_id is None:
                return "ok"

            file_ids = self._extract_photo_file_ids(payload)
            if not file_ids:
                return "ok"

            actor = self.resolve_actor_identity_use_case.execute(
                platform_user_id=from_id,
                username=self._extract_username(payload),
            )
            if actor is None or actor.platform_user_id is None:
                return "employee_not_allowed"

            employee = self.employee_repository.find_active_by_platform_user_id(actor.platform_user_id)
            if employee is None:
                return "employee_not_allowed"

            for file_id in file_ids:
                self.user_draft_repository.add_photo(user_id=actor.platform_user_id, file_id=file_id)

            draft_count = self.user_draft_repository.count_photos_by_user_id(actor.platform_user_id)
            return f"draft_updated:{draft_count}"

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
    def _extract_photo_file_ids(payload: dict[str, Any]) -> list[str]:
        event_object = payload.get("object")
        if not isinstance(event_object, dict):
            return []

        message = event_object.get("message") if isinstance(event_object.get("message"), dict) else event_object
        attachments = message.get("attachments") if isinstance(message, dict) else None

        if not isinstance(attachments, list):
            return []

        file_ids: list[str] = []
        for attachment in attachments:
            file_id = ProcessVkCallbackUseCase._normalize_photo_file_id(attachment)
            if file_id:
                file_ids.append(file_id)

        return file_ids

    @staticmethod
    def _normalize_photo_file_id(attachment: Any) -> str | None:
        if not isinstance(attachment, dict) or attachment.get("type") != "photo":
            return None

        photo = attachment.get("photo")
        if not isinstance(photo, dict):
            return None

        ready_file_id = photo.get("file_id")
        if isinstance(ready_file_id, str) and ready_file_id.strip():
            return ready_file_id.strip()

        owner_id = photo.get("owner_id")
        photo_id = photo.get("id")
        if not isinstance(owner_id, int) or not isinstance(photo_id, int):
            return None

        access_key = photo.get("access_key")
        if isinstance(access_key, str) and access_key.strip():
            return f"photo{owner_id}_{photo_id}_{access_key.strip()}"

        return f"photo{owner_id}_{photo_id}"

    @staticmethod
    def _extract_username(payload: dict[str, Any]) -> str:
        event_object = payload.get("object")
        if not isinstance(event_object, dict):
            return ""

        message = event_object.get("message")
        message_dict = message if isinstance(message, dict) else event_object
        username = message_dict.get("username")
        return username if isinstance(username, str) else ""
