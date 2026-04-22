from typing import Any

from infrastructure.logger import get_logger, payload_summary
from interfaces.admin_handler import AdminHandler
from use_cases.process_vk_callback import ProcessVkCallbackUseCase


class VkCallbackHandler:
    """Транспортный адаптер: разбирает HTTP/VK input и делегирует use case."""

    def __init__(
        self,
        process_vk_callback_use_case: ProcessVkCallbackUseCase,
        confirmation_code: str,
        callback_secret: str,
        admin_user_ids: tuple[int, ...],
        admin_handler: AdminHandler,
    ) -> None:
        self._process_vk_callback_use_case = process_vk_callback_use_case
        self._confirmation_code = confirmation_code
        self._callback_secret = callback_secret
        self._admin_user_ids = set(admin_user_ids)
        self._admin_handler = admin_handler
        self._logger = get_logger()

    def handle(self, request_json: dict[str, Any]) -> str:
        self._logger.info("Incoming VK callback: %s", payload_summary(request_json))
        event_type = str(request_json.get("type", ""))
        validation_error = self._validate_request(request_json, event_type)
        if validation_error is not None:
            self._logger.warning("Callback rejected: %s", validation_error)
            return "ok"

        result = self._process_vk_callback_use_case.execute(
            event_type=event_type,
            payload=request_json,
        )

        if event_type == "message_new" and result != "duplicate_event":
            self._handle_admin_commands(request_json)

        if result == "need_confirmation_code":
            return self._confirmation_code

        if result.startswith("draft_updated:"):
            draft_count = result.split(":", maxsplit=1)[1]
            return f"Фото сохранены в черновик. Всего фото: {draft_count}"

        if result.startswith("draft_cleared:"):
            deleted_count = result.split(":", maxsplit=1)[1]
            return f"Черновик очищен. Удалено фото: {deleted_count}"

        if result == "draft_empty":
            return "Черновик пуст — отправлять нечего."

        if result.startswith("draft_submitted:"):
            _, queued_count, employee_id = result.split(":", maxsplit=2)
            return (
                "Черновик отправлен в очередь. "
                f"Фото в очереди: {queued_count}. "
                f"employee_id: {employee_id}"
            )

        return "ok"

    def _validate_request(self, request_json: dict[str, Any], event_type: str) -> str | None:
        if not event_type:
            return "missing event type"

        request_secret = request_json.get("secret")
        if event_type == "confirmation":
            if request_secret is None:
                return None
            if not isinstance(request_secret, str):
                return "invalid secret format for confirmation event"
            if request_secret != self._callback_secret:
                return "secret mismatch for confirmation event"
            return None

        if not isinstance(request_secret, str):
            return "missing secret"
        if request_secret != self._callback_secret:
            return "secret mismatch"

        return None

    def _handle_admin_commands(self, request_json: dict[str, Any]) -> None:
        event_object = request_json.get("object")
        if not isinstance(event_object, dict):
            return

        message = event_object.get("message")
        message_dict = message if isinstance(message, dict) else event_object

        from_id = message_dict.get("from_id")
        text = message_dict.get("text")
        if not isinstance(from_id, int) or not isinstance(text, str):
            return

        if from_id not in self._admin_user_ids:
            return

        try:
            admin_result = self._admin_handler.handle_text(text=text, from_id=from_id)
        except Exception:  # noqa: BLE001
            self._logger.exception("Admin command failed: from_id=%s text=%s", from_id, text)
            return

        self._logger.info("Admin command processed: from_id=%s result=%s", from_id, admin_result)
