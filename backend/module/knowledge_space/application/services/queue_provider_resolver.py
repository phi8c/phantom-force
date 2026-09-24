from __future__ import annotations

from uuid import UUID

from module.knowledge_space.domain.contracts.knowledge_space_queue_repository import (
    KnowledgeSpaceQueueRepository,
)
from module.knowledge_space.domain.contracts.queue_provider_resolver import (
    QueueProviderResolver,
)


class QueueProviderConfigurationError(ValueError):
    pass


class KnowledgeSpaceQueueProviderResolver(QueueProviderResolver):
    def __init__(
        self,
        repository: KnowledgeSpaceQueueRepository,
        *,
        fallback_provider_code: str,
    ) -> None:
        self._repository = repository
        self._fallback_provider_code = self._normalize_code(
            fallback_provider_code,
            field_name="fallback queue provider",
        )

    async def resolve(self, knowledge_space_id: UUID) -> str:
        mapping = await self._repository.get_default_for_knowledge_space(
            knowledge_space_id
        )
        if mapping is None:
            return self._fallback_provider_code
        if not mapping.enabled:
            raise QueueProviderConfigurationError(
                "Default Knowledge Space queue mapping is disabled."
            )
        if mapping.provider is None:
            raise QueueProviderConfigurationError(
                "Default Knowledge Space queue provider does not exist."
            )
        if not mapping.provider.enabled:
            raise QueueProviderConfigurationError(
                f"Queue provider '{mapping.provider.code}' is disabled."
            )
        return self._normalize_code(
            mapping.provider.code,
            field_name="queue provider code",
        )

    @staticmethod
    def _normalize_code(value: str, *, field_name: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise QueueProviderConfigurationError(
                f"{field_name} must not be empty."
            )
        return normalized
