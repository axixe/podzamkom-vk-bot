from __future__ import annotations

import logging
from typing import Any


LOGGER_NAME = "podzamkom_vk_bot"


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def mask_secret(value: str) -> str:
    if not value:
        return "<empty>"
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}***{value[-2:]}"


def payload_summary(payload: dict[str, Any]) -> str:
    object_value = payload.get("object")
    object_keys: list[str] = []
    if isinstance(object_value, dict):
        object_keys = sorted(str(key) for key in object_value.keys())

    return (
        f"type={payload.get('type', '<missing>')!r}, "
        f"event_id={payload.get('event_id', '<missing>')!r}, "
        f"object_keys={object_keys}"
    )
