from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigError(ValueError):
    """Ошибка конфигурации приложения."""


@dataclass(frozen=True)
class AppConfig:
    vk_token: str
    vk_callback_secret: str
    vk_admin_ids: tuple[int, ...]
    db_path: Path
    vk_confirmation_code: str

    @classmethod
    def from_env(cls) -> "AppConfig":
        required_envs = [
            "VK_TOKEN",
            "VK_CALLBACK_SECRET",
            "VK_ADMIN_IDS",
            "DB_PATH",
            "VK_CONFIRMATION_CODE",
        ]
        missing = [key for key in required_envs if not os.getenv(key)]
        if missing:
            raise ConfigError(
                "Missing required environment variables: " + ", ".join(missing)
            )

        raw_admin_ids = os.environ["VK_ADMIN_IDS"]
        try:
            admin_ids = tuple(
                int(value.strip())
                for value in raw_admin_ids.split(",")
                if value.strip()
            )
        except ValueError as exc:
            raise ConfigError(
                "VK_ADMIN_IDS must be a comma-separated list of integers. "
                f"Got: {raw_admin_ids!r}"
            ) from exc

        if not admin_ids:
            raise ConfigError(
                "VK_ADMIN_IDS must contain at least one integer id."
            )

        return cls(
            vk_token=os.environ["VK_TOKEN"],
            vk_callback_secret=os.environ["VK_CALLBACK_SECRET"],
            vk_admin_ids=admin_ids,
            db_path=Path(os.environ["DB_PATH"]),
            vk_confirmation_code=os.environ["VK_CONFIRMATION_CODE"],
        )
