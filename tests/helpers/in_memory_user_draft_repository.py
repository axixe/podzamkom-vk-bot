class InMemoryUserDraftRepository:
    def __init__(self) -> None:
        self._drafts: dict[int, list[str]] = {}

    def add_photo(self, user_id: int, file_id: str) -> None:
        self._drafts.setdefault(user_id, []).append(file_id)

    def count_photos_by_user_id(self, user_id: int) -> int:
        return len(self._drafts.get(user_id, []))

    def clear_by_user_id(self, user_id: int) -> int:
        deleted = len(self._drafts.get(user_id, []))
        self._drafts.pop(user_id, None)
        return deleted

    @property
    def drafts(self) -> dict[int, list[str]]:
        return self._drafts
