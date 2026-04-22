from typing import Any

from infrastructure.logger import get_logger, payload_summary
from use_cases.process_vk_callback import ProcessVkCallbackUseCase


class VkCallbackHandler:
    """Транспортный адаптер: разбирает HTTP/VK input и делегирует use case."""

    def __init__(
        self,
        process_vk_callback_use_case: ProcessVkCallbackUseCase,
        confirmation_code: str,
        callback_secret: str,
    ) -> None:
        self._process_vk_callback_use_case = process_vk_callback_use_case
        self._confirmation_code = confirmation_code
        self._callback_secret = callback_secret
        self._logger = get_logger()

    def handle(self, request_json: dict[str, Any]) -> str:
        self._logger.info("Incoming VK callback: %s", payload_summary(request_json))

        request_secret = str(request_json.get("secret", ""))
        if request_secret != self._callback_secret:
            self._logger.warning("Callback rejected: secret mismatch")
            return "forbidden"

        event_type = str(request_json.get("type", ""))

        result = self._process_vk_callback_use_case.execute(
            event_type=event_type,
            payload=request_json,
        )

        if result == "need_confirmation_code":
            return self._confirmation_code

        return "ok"
