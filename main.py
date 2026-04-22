"""Пример wiring приложения и вызова callback handler."""

from infrastructure.bootstrap import build_container
from infrastructure.config import AppConfig, ConfigError
from infrastructure.logger import configure_logging, get_logger, mask_secret
from interfaces.vk_callback_handler import VkCallbackHandler


if __name__ == "__main__":
    configure_logging()
    logger = get_logger()

    try:
        config = AppConfig.from_env()
    except ConfigError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc

    logger.info(
        "Configuration loaded: db_path=%s, admin_user_ids=%s, vk_token=%s, callback_secret=%s",
        config.db_path,
        config.admin_user_ids,
        mask_secret(config.vk_token),
        mask_secret(config.vk_callback_secret),
    )

    container = build_container(config)
    handler = VkCallbackHandler(
        process_vk_callback_use_case=container.process_vk_callback_use_case,
        confirmation_code=config.vk_confirmation_code,
        callback_secret=config.vk_callback_secret,
        admin_user_ids=config.admin_user_ids,
        admin_handler=container.admin_handler,
    )

    print(
        handler.handle(
            {
                "type": "confirmation",
                "secret": config.vk_callback_secret,
                "event_id": "demo-confirmation",
            }
        )
    )
    print(
        handler.handle(
            {
                "type": "message_new",
                "secret": config.vk_callback_secret,
                "event_id": "demo-message",
                "object": {"text": "hello"},
            }
        )
    )
