from __future__ import annotations

from collections.abc import AsyncIterator

from module.data_platform.data_hub.application.services.data_hub_service import (
    DataHubService,
)
from module.data_platform.data_hub.domain.entities.discovered_file import (
    DiscoveredFile,
)
from module.data_platform.data_hub.domain.value_objects.source_reference import (
    SourceReference,
)


class DataHub:
    """
    Public in-process API of the Data Hub module.

    Other modules must depend on this API instead of importing
    application use cases or infrastructure providers directly.
    """

    def __init__(
        self,
        service: DataHubService,
    ) -> None:
        self._service = service

    async def discover_files(
        self,
        source: SourceReference,
    ) -> AsyncIterator[DiscoveredFile]:
        async for discovered_file in self._service.discover_files(source):
            yield discovered_file

    async def download_file(
        self,
        file: DiscoveredFile,
    ) -> bytes:
        return await self._service.download_file(file)