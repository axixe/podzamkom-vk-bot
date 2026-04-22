from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from infrastructure.bootstrap import build_container
from infrastructure.config import AppConfig, ConfigError
from infrastructure.logger import configure_logging, get_logger, mask_secret
from interfaces.vk_callback_handler import VkCallbackHandler


class CallbackRequestHandler(BaseHTTPRequestHandler):
    vk_handler: VkCallbackHandler

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/callback":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"not found")
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"invalid json")
            return

        response_text = self.vk_handler.handle(payload)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(response_text.encode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"not found")

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def create_http_server(port: int = 8000) -> ThreadingHTTPServer:
    configure_logging()
    logger = get_logger()

    try:
        config = AppConfig.from_env()
    except ConfigError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc

    logger.info(
        "Starting callback server: port=%s, db_path=%s, admin_user_ids=%s, vk_token=%s, callback_secret=%s",
        port,
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

    CallbackRequestHandler.vk_handler = handler
    return ThreadingHTTPServer(("0.0.0.0", port), CallbackRequestHandler)


if __name__ == "__main__":
    server = create_http_server(port=8000)
    print("Callback server listening on http://0.0.0.0:8000/callback")
    server.serve_forever()
