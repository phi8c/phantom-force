from __future__ import annotations

from collections.abc import AsyncIterator

from module.data_platform.data_hub.shared.domain.contracts.discovery_provider import DiscoveryProvider
from module.data_platform.data_hub.shared.domain.entities.discovered_file import DiscoveredFile
from module.data_platform.data_hub.shared.domain.value_objects.source_reference import SourceReference


class DiscoverFilesUseCase:
    def __init__(
        self,
        discovery_provider: DiscoveryProvider,
    ) -> None:
        self._discovery_provider = discovery_provider

    async def execute(
        self,
        source: SourceReference,
    ) -> AsyncIterator[DiscoveredFile]:
        async for discovered_file in self._discovery_provider.discover(
            source,
        ):
            yield discovered_file
