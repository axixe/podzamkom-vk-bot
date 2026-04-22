from dataclasses import dataclass

from domain.models import ActorIdentity
from domain.repositories import ActorIdentityRepository


class ResolveActorIdentityError(Exception):
    """Базовая бизнес-ошибка use case ResolveActorIdentity."""


class AmbiguousUsernameError(ResolveActorIdentityError):
    """Невозможно однозначно сопоставить username c одним актором."""

    def __init__(self, username: str) -> None:
        super().__init__(f"Ambiguous username: {username}")
        self.username = username


@dataclass(slots=True)
class ResolveActorIdentityUseCase:
    """Разрешает доменную идентичность: сначала по platform_user_id, затем по username."""

    actor_identity_repository: ActorIdentityRepository

    def execute(self, platform_user_id: int, username: str) -> ActorIdentity | None:
        actor = self.actor_identity_repository.find_by_platform_user_id(platform_user_id)
        if actor is not None:
            return actor

        matches = self.actor_identity_repository.find_by_username(username)
        if not matches:
            return None

        if len(matches) > 1:
            raise AmbiguousUsernameError(username)

        matched_actor = matches[0]
        return self.actor_identity_repository.link_platform_user_id(
            actor_id=matched_actor.actor_id,
            platform_user_id=platform_user_id,
        )
