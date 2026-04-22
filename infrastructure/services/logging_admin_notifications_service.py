from dataclasses import dataclass
import logging


@dataclass(slots=True)
class LoggingAdminNotificationsService:
    admin_user_ids: tuple[int, ...]
    logger: logging.Logger

    def notify_submit_draft(self, queued_count: int) -> None:
        message = (
            f"Новая отправка в очередь: +{queued_count}. "
            "Возьмите следующий элемент командой «Следующий»."
        )
        for admin_user_id in self.admin_user_ids:
            self.logger.info(
                "Admin notification queued: admin_user_id=%s message=%s",
                admin_user_id,
                message,
            )
