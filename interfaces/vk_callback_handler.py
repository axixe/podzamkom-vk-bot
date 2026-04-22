from typing import Any

from use_cases.process_vk_callback import ProcessVkCallbackUseCase


class VkCallbackHandler:
    """Транспортный адаптер: разбирает HTTP/VK input и делегирует use case."""

    def __init__(
        self,
        process_vk_callback_use_case: ProcessVkCallbackUseCase,
        confirmation_code: str,
    ) -> None:
        self._process_vk_callback_use_case = process_vk_callback_use_case
        self._confirmation_code = confirmation_code

    def handle(self, request_json: dict[str, Any]) -> str:
        event_type = str(request_json.get("type", ""))

        result = self._process_vk_callback_use_case.execute(
            event_type=event_type,
            payload=request_json,
        )

        if result == "need_confirmation_code":
            return self._confirmation_code

        return "ok"
