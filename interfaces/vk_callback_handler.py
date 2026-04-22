import json
from typing import Any

from domain.services import OutgoingMessageService
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
        outgoing_message_service: OutgoingMessageService,
    ) -> None:
        self._process_vk_callback_use_case = process_vk_callback_use_case
        self._confirmation_code = confirmation_code
        self._callback_secret = callback_secret
        self._admin_user_ids = set(admin_user_ids)
        self._admin_handler = admin_handler
        self._outgoing_message_service = outgoing_message_service
        self._logger = get_logger()

    def handle(self, request_json: dict[str, Any]) -> str:
        self._logger.info("Incoming VK callback: %s", payload_summary(request_json))
        event_type_raw = request_json.get("type")
        event_type = event_type_raw if isinstance(event_type_raw, str) else ""
        correlation_id = self._extract_correlation_id(request_json)
        validation_error = self._validate_request(request_json, event_type)
        if validation_error is not None:
            self._logger.warning(
                "Callback rejected: correlation_id=%s error=%s",
                correlation_id,
                validation_error,
            )
            return "ok"

        if event_type not in {"confirmation", "message_new"}:
            self._logger.info(
                "Ignoring unsupported event type: correlation_id=%s event_type=%s",
                correlation_id,
                event_type,
            )
            return "ok"

        result = self._process_vk_callback_use_case.execute(
            event_type=event_type,
            payload=request_json,
        )

        if event_type == "message_new" and result != "duplicate_event":
            self._handle_admin_commands(request_json)

        if result == "need_confirmation_code":
            return self._confirmation_code

        if result == "show_main_menu":
            self._send_message_new_reply(
                request_json,
                self._render_employee_menu_message(),
                self._main_menu_keyboard(),
            )
            return "ok"

        if result == "show_main_menu:admin":
            self._send_message_new_reply(
                request_json,
                self._render_admin_menu_message(),
                self._main_menu_keyboard(),
            )
            return "ok"

        if result == "employee_not_allowed":
            self._send_message_new_reply(
                request_json,
                "Доступ закрыт. У вас нет роли в системе.",
                self._main_menu_keyboard(),
            )
            return "ok"

        if result.startswith("draft_updated:"):
            draft_count = result.split(":", maxsplit=1)[1]
            self._send_message_new_reply(request_json, self._with_main_menu(f"Фото сохранены в черновик. Всего фото: {draft_count}"), self._main_menu_keyboard())
            return "ok"

        if result.startswith("draft_cleared:"):
            deleted_count = result.split(":", maxsplit=1)[1]
            self._send_message_new_reply(
                request_json,
                self._with_main_menu(f"Черновик очищен. Удалено фото: {deleted_count}"),
                self._main_menu_keyboard(),
            )
            return "ok"

        if result == "draft_empty":
            self._send_message_new_reply(
                request_json,
                self._with_main_menu("Черновик пуст — отправлять нечего."),
                self._main_menu_keyboard(),
            )
            return "ok"

        if result.startswith("draft_submitted:"):
            _, queued_count, employee_id = result.split(":", maxsplit=2)
            self._send_message_new_reply(
                request_json,
                self._with_main_menu(
                    "Черновик отправлен в очередь. "
                    f"Фото в очереди: {queued_count}. "
                    f"employee_id: {employee_id}"
                ),
                self._main_menu_keyboard(),
            )
            return "ok"

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

        event_id = request_json.get("event_id")
        if not isinstance(event_id, str) or not event_id.strip():
            return "missing event_id"

        if event_type == "message_new":
            return self._validate_message_new_fields(request_json)

        return None

    @staticmethod
    def _extract_correlation_id(request_json: dict[str, Any]) -> str:
        correlation_id = request_json.get("event_id")
        if isinstance(correlation_id, str) and correlation_id.strip():
            return correlation_id.strip()
        return "<missing-event-id>"

    @staticmethod
    def _validate_message_new_fields(request_json: dict[str, Any]) -> str | None:
        event_object = request_json.get("object")
        if not isinstance(event_object, dict):
            return "missing object payload"

        message = event_object.get("message")
        message_dict = message if isinstance(message, dict) else event_object

        from_id = message_dict.get("from_id")
        if not isinstance(from_id, int):
            return "missing actor/user identifier (from_id)"

        has_attachments = isinstance(message_dict.get("attachments"), list)
        has_payload = "payload" in message_dict
        text_value = message_dict.get("text")
        has_text = isinstance(text_value, str) and bool(text_value.strip())
        if not has_attachments and not has_payload and not has_text:
            return "missing attachments/payload/text"

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

    def _render_employee_menu_message(self) -> str:
        return (
            "Главное меню сотрудника:\n"
            "• Отправьте фото в чат, чтобы добавить их в черновик.\n"
            "• /submit — отправить черновик на проверку.\n"
            "• /clear — очистить черновик."
        )

    def _render_admin_menu_message(self) -> str:
        return (
            "Главное меню администратора:\n"
            "• /next — взять следующий элемент на проверку.\n"
            "• /approve <id> — подтвердить элемент.\n"
            "• /reject <id> <reason> — отклонить элемент."
        )

    def _with_main_menu(self, message: str) -> str:
        return f"{message}\n\n🏠 Главное меню"

    def _send_message_new_reply(self, request_json: dict[str, Any], text: str, keyboard: str | None = None) -> None:
        user_id = self._extract_from_id(request_json)
        if user_id is None:
            self._logger.warning("Cannot send message: missing from_id")
            return

        try:
            self._outgoing_message_service.send_message(user_id=user_id, text=text, keyboard=keyboard)
        except Exception:  # noqa: BLE001
            self._logger.exception("Failed to send VK message with keyboard: user_id=%s", user_id)
            if keyboard is None:
                return

            try:
                self._outgoing_message_service.send_message(user_id=user_id, text=text, keyboard=None)
            except Exception:  # noqa: BLE001
                self._logger.exception("Failed to send VK message without keyboard: user_id=%s", user_id)

    @staticmethod
    def _extract_from_id(request_json: dict[str, Any]) -> int | None:
        event_object = request_json.get("object")
        if not isinstance(event_object, dict):
            return None

        message = event_object.get("message")
        message_dict = message if isinstance(message, dict) else event_object
        from_id = message_dict.get("from_id")
        if isinstance(from_id, int):
            return from_id
        return None

    @staticmethod
    def _main_menu_keyboard() -> str:
        keyboard = {
            "one_time": False,
            "buttons": [
                [
                    {"action": {"type": "text", "label": "🏠 Главное меню"}, "color": "positive"},
                ],
            ],
        }
        return json.dumps(keyboard, ensure_ascii=False)
