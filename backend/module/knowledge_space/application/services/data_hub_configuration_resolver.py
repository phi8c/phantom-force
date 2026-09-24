from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from uuid import UUID

from module.knowledge_space.domain.contracts.knowledge_space_data_hub_repository import (
    KnowledgeSpaceDataHubRepository,
)
from module.master_data.data_hub_providers.domain.contracts.data_hub_provider_repository import (
    DataHubProviderRepository,
)


class DataHubConfigurationNotFoundError(LookupError):
    pass


class DataHubConfigurationDisabledError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ResolvedDataHubConfiguration:
    data_hub_id: UUID
    provider: str
    configuration: Mapping[str, Any]


class KnowledgeSpaceDataHubConfigurationResolver:
    def __init__(
        self,
        data_hub_repository: KnowledgeSpaceDataHubRepository,
        provider_repository: DataHubProviderRepository,
    ) -> None:
        self._data_hub_repository = data_hub_repository
        self._provider_repository = provider_repository

    async def resolve(
        self,
        knowledge_space_id: UUID,
    ) -> ResolvedDataHubConfiguration:
        data_hub = await self._data_hub_repository.get_by_knowledge_space_id(
            knowledge_space_id
        )
        if data_hub is None or data_hub.id is None:
            raise DataHubConfigurationNotFoundError(
                f"Knowledge Space '{knowledge_space_id}' has no Data Hub configuration."
            )
        if not data_hub.enabled:
            raise DataHubConfigurationDisabledError(
                f"Data Hub for Knowledge Space '{knowledge_space_id}' is disabled."
            )

        provider = await self._provider_repository.get_by_id(
            data_hub.data_hub_provider_id
        )
        if provider is None:
            raise DataHubConfigurationNotFoundError(
                f"Data Hub provider '{data_hub.data_hub_provider_id}' was not found."
            )
        if not provider.enabled:
            raise DataHubConfigurationDisabledError(
                f"Data Hub provider '{provider.code}' is disabled."
            )

        provider_code = (provider.provider or provider.code).strip().lower()
        if not provider_code:
            raise ValueError("Data Hub provider code must not be empty.")
        return ResolvedDataHubConfiguration(
            data_hub_id=data_hub.id,
            provider=provider_code,
            configuration=dict(data_hub.configuration or {}),
        )
