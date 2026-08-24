from __future__ import annotations

from collections.abc import AsyncIterator

from module.data_platform.data_hub.domain.entities.discovered_file import DiscoveredFile
from module.data_platform.data_hub.domain.value_objects.source_reference import SourceReference
from module.data_platform.data_hub.application.use_cases.discovery_files import DiscoverFilesUseCase
from module.data_platform.data_hub.application.use_cases.download_file import DownloadFileUseCase


class DataHubService:
    def __init__(
        self,
        discover_files: DiscoverFilesUseCase,
        download_file: DownloadFileUseCase,
    ) -> None:
        self._discover_files = discover_files
        self._download_file = download_file

    async def discover_files(
        self,
        source: SourceReference,
    ) -> AsyncIterator[DiscoveredFile]:
        async for discovered_file in self._discover_files.execute(source):
            yield discovered_file

    async def download_file(
        self,
        file: DiscoveredFile,
    ) -> bytes:
        return await self._download_file.execute(file)