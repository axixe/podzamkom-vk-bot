from dataclasses import dataclass

from domain.repositories import UserDraftRepository


@dataclass(slots=True)
class ClearDraftUseCase:
    user_draft_repository: UserDraftRepository

    def execute(self, user_id: int) -> int:
        return self.user_draft_repository.clear_by_user_id(user_id)
