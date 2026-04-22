from domain.models import ActorIdentity


class InMemoryActorIdentityRepository:
    """In-memory репозиторий акторов для тестов и локальной разработки."""

    def __init__(self, actors: list[ActorIdentity] | None = None) -> None:
        self._actors: dict[int, ActorIdentity] = {
            actor.actor_id: actor for actor in (actors or [])
        }

    def find_by_platform_user_id(self, platform_user_id: int) -> ActorIdentity | None:
        for actor in self._actors.values():
            if actor.platform_user_id == platform_user_id:
                return actor

        return None

    def find_by_username(self, username: str) -> list[ActorIdentity]:
        return [actor for actor in self._actors.values() if actor.username == username]

    def link_platform_user_id(self, actor_id: int, platform_user_id: int) -> ActorIdentity:
        actor = self._actors[actor_id]
        updated = ActorIdentity(
            actor_id=actor.actor_id,
            username=actor.username,
            platform_user_id=platform_user_id,
        )
        self._actors[actor_id] = updated
        return updated
