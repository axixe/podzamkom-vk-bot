class InMemoryProcessedEventRepository:
    def __init__(self) -> None:
        self._processed_ids: set[str] = set()

    def mark_processed_if_new(self, event_id: str) -> bool:
        if event_id in self._processed_ids:
            return False

        self._processed_ids.add(event_id)
        return True
