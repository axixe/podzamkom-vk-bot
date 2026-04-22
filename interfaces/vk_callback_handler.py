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

        request_secret = str(request_json.get("secret", ""))
        if request_secret != self._callback_secret:
            self._logger.warning("Callback rejected: secret mismatch")
            return "forbidden"

        event_type = str(request_json.get("type", ""))

        if event_type == "message_new":
            self._handle_admin_commands(request_json)

        result = self._process_vk_callback_use_case.execute(
            event_type=event_type,
            payload=request_json,
        )

        if result == "need_confirmation_code":
            return self._confirmation_code

        if result.startswith("draft_updated:"):
            draft_count = result.split(":", maxsplit=1)[1]
            return f"Фото сохранены в черновик. Всего фото: {draft_count}"

        if result.startswith("draft_cleared:"):
            deleted_count = result.split(":", maxsplit=1)[1]
            return f"Черновик очищен. Удалено фото: {deleted_count}"

        return "ok"

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
            admin_result = self._admin_handler.handle_text(text)
        except Exception:  # noqa: BLE001
            self._logger.exception("Admin command failed: from_id=%s text=%s", from_id, text)
            return

        self._logger.info("Admin command processed: from_id=%s result=%s", from_id, admin_result)
