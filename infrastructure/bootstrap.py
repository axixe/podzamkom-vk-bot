from dataclasses import dataclass

from infrastructure.repositories.in_memory_event_repository import InMemoryEventRepository
from use_cases.process_vk_callback import ProcessVkCallbackUseCase


@dataclass(frozen=True)
class AppContainer:
    """Composition root: связывает реализации инфраструктуры и use cases."""

    event_repository: InMemoryEventRepository
    process_vk_callback_use_case: ProcessVkCallbackUseCase


def build_container() -> AppContainer:
    event_repository = InMemoryEventRepository()
    process_vk_callback_use_case = ProcessVkCallbackUseCase(
        event_repository=event_repository,
    )

    return AppContainer(
        event_repository=event_repository,
        process_vk_callback_use_case=process_vk_callback_use_case,
    )
