import unittest

from domain.models import ActorIdentity
from infrastructure.repositories.in_memory_actor_identity_repository import (
    InMemoryActorIdentityRepository,
)
from use_cases.identity.resolve_actor_identity import (
    AmbiguousUsernameError,
    ResolveActorIdentityUseCase,
)


class ResolveActorIdentityUseCaseTest(unittest.TestCase):
    def test_found_by_platform_user_id(self) -> None:
        repository = InMemoryActorIdentityRepository(
            actors=[
                ActorIdentity(actor_id=1, username="alice", platform_user_id=42),
            ]
        )
        use_case = ResolveActorIdentityUseCase(actor_identity_repository=repository)

        result = use_case.execute(platform_user_id=42, username="alice")

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.actor_id, 1)
        self.assertEqual(result.platform_user_id, 42)

    def test_links_platform_user_id_by_username_when_single_match(self) -> None:
        repository = InMemoryActorIdentityRepository(
            actors=[
                ActorIdentity(actor_id=2, username="bob", platform_user_id=None),
            ]
        )
        use_case = ResolveActorIdentityUseCase(actor_identity_repository=repository)

        result = use_case.execute(platform_user_id=77, username="bob")

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.actor_id, 2)
        self.assertEqual(result.platform_user_id, 77)

    def test_returns_none_when_not_found(self) -> None:
        repository = InMemoryActorIdentityRepository(
            actors=[
                ActorIdentity(actor_id=3, username="charlie", platform_user_id=None),
            ]
        )
        use_case = ResolveActorIdentityUseCase(actor_identity_repository=repository)

        result = use_case.execute(platform_user_id=88, username="unknown")

        self.assertIsNone(result)

    def test_raises_business_error_on_ambiguous_username_without_linking(self) -> None:
        repository = InMemoryActorIdentityRepository(
            actors=[
                ActorIdentity(actor_id=4, username="dana", platform_user_id=None),
                ActorIdentity(actor_id=5, username="dana", platform_user_id=None),
            ]
        )
        use_case = ResolveActorIdentityUseCase(actor_identity_repository=repository)

        with self.assertRaises(AmbiguousUsernameError):
            use_case.execute(platform_user_id=99, username="dana")

        self.assertIsNone(repository.find_by_platform_user_id(99))


if __name__ == "__main__":
    unittest.main()
