"""Пример wiring приложения и вызова callback handler."""

from infrastructure.bootstrap import build_container
from interfaces.vk_callback_handler import VkCallbackHandler


if __name__ == "__main__":
    container = build_container()
    handler = VkCallbackHandler(
        process_vk_callback_use_case=container.process_vk_callback_use_case,
        confirmation_code="test-confirmation-code",
    )

    print(handler.handle({"type": "confirmation"}))
    print(handler.handle({"type": "message_new", "object": {"text": "hello"}}))
