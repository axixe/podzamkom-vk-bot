from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from random import randint


@dataclass(slots=True)
class VkApiOutgoingMessageService:
    """Отправка сообщений пользователю через VK API messages.send."""

    vk_token: str
    api_version: str = "5.199"

    def send_message(self, user_id: int, text: str, keyboard: str | None = None) -> None:
        payload: dict[str, str | int] = {
            "user_id": user_id,
            "message": text,
            "random_id": randint(1, 2_147_483_647),
            "access_token": self.vk_token,
            "v": self.api_version,
        }
        if keyboard:
            payload["keyboard"] = keyboard

        encoded = urllib.parse.urlencode(payload).encode("utf-8")
        request = urllib.request.Request(
            url="https://api.vk.com/method/messages.send",
            data=encoded,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10) as response:  # nosec B310
            body = response.read().decode("utf-8")

        decoded = json.loads(body)
        if "error" in decoded:
            raise RuntimeError(f"VK API error: {decoded['error']}")
