class SpyAdminNotificationsService:
    def __init__(self) -> None:
        self.notified_queued_counts: list[int] = []

    def notify_submit_draft(self, queued_count: int) -> None:
        self.notified_queued_counts.append(queued_count)
