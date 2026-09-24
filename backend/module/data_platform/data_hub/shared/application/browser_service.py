from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol
from uuid import UUID

from module.knowledge_space.application.services.data_hub_configuration_resolver import (
    KnowledgeSpaceDataHubConfigurationResolver,
    ResolvedDataHubConfiguration,
)

from ..domain.contracts.browser import DataHubBrowser
from ..domain.entities.browse_node import DataHubBrowseNode


class BrowserProviderRegistry(Protocol):
    def create(
        self,
        resolved: ResolvedDataHubConfiguration,
    ) -> DataHubBrowser:
        ...


@dataclass(frozen=True, slots=True)
class BrowseResult:
    provider: str
    nodes: list[DataHubBrowseNode]


class DataHubBrowserService:
    def __init__(
        self,
        configuration_resolver: KnowledgeSpaceDataHubConfigurationResolver,
        provider_registry: BrowserProviderRegistry,
    ) -> None:
        self._configuration_resolver = configuration_resolver
        self._provider_registry = provider_registry

    async def browse_root(self, knowledge_space_id: UUID) -> BrowseResult:
        return await self._browse(knowledge_space_id, None)

    async def browse_children(
        self,
        knowledge_space_id: UUID,
        locator: Mapping[str, Any],
    ) -> BrowseResult:
        return await self._browse(knowledge_space_id, locator)

    async def _browse(
        self,
        knowledge_space_id: UUID,
        locator: Mapping[str, Any] | None,
    ) -> BrowseResult:
        resolved = await self._configuration_resolver.resolve(knowledge_space_id)
        browser = self._provider_registry.create(resolved)
        try:
            nodes = (
                await browser.browse_root()
                if locator is None
                else await browser.browse_children(locator)
            )
        finally:
            await browser.close()
        return BrowseResult(provider=resolved.provider, nodes=nodes)
