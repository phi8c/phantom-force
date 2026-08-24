from __future__ import annotations

from collections.abc import AsyncIterator

from ...domain.contracts.discovery_provider import DiscoveryProvider
from ...domain.entities.discovered_file import DiscoveredFile
from ...domain.value_objects.source_reference import SourceReference


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