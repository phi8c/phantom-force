from __future__ import annotations

import logging
from uuid import UUID

from module.knowledge_space.domain.contracts.knowledge_space_queue_repository import (
    KnowledgeSpaceQueueRepository,
)
from module.knowledge_space.domain.contracts.queue_provider_resolver import (
    QueueProviderResolver,
)


logger = logging.getLogger(__name__)


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
        logger.info(
            "queue provider lookup_result knowledge_space_id=%s mapping_found=%s mapping_enabled=%s provider_found=%s provider_code=%s provider_enabled=%s",
            knowledge_space_id,
            mapping is not None,
            getattr(mapping, "enabled", None),
            getattr(mapping, "provider", None) is not None,
            getattr(getattr(mapping, "provider", None), "code", None),
            getattr(getattr(mapping, "provider", None), "enabled", None),
        )
        if mapping is None:
            logger.info(
                "queue provider fallback knowledge_space_id=%s queue_provider=%s",
                knowledge_space_id,
                self._fallback_provider_code,
            )
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
        provider_code = self._normalize_code(
            mapping.provider.code,
            field_name="queue provider code",
        )
        logger.info(
            "queue provider mapping knowledge_space_id=%s queue_provider=%s",
            knowledge_space_id,
            provider_code,
        )
        return provider_code

    @staticmethod
    def _normalize_code(value: str, *, field_name: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise QueueProviderConfigurationError(
                f"{field_name} must not be empty."
            )
        return normalized
