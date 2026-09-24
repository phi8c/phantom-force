from __future__ import annotations

from collections.abc import AsyncIterator

from module.data_platform.data_hub.shared.domain.entities.discovered_file import DiscoveredFile
from module.data_platform.data_hub.shared.domain.value_objects.source_reference import SourceReference
from module.data_platform.data_hub.sharepoint.application.use_cases.browse_sharepoint import BrowseSharePointUseCase
from module.data_platform.data_hub.sharepoint.application.use_cases.discovery_files import DiscoverFilesUseCase
from module.data_platform.data_hub.sharepoint.application.use_cases.download_file import DownloadFileUseCase
from module.data_platform.data_hub.sharepoint.domain.entities.browse_node import BrowseNode


class DataHubService:
    def __init__(
        self,
        discover_files: DiscoverFilesUseCase,
        download_file: DownloadFileUseCase,
        browse_sharepoint: BrowseSharePointUseCase | None = None,
    ) -> None:
        self._discover_files = discover_files
        self._download_file = download_file
        self._browse_sharepoint = browse_sharepoint

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
    
    
    async def download_stream(
        self,
        file: DiscoveredFile,
    ) -> AsyncIterator[bytes]:

        async for chunk in self._download_file.execute(
            file
        ):
            yield chunk

    def _sharepoint_browser(self) -> BrowseSharePointUseCase:
        if self._browse_sharepoint is None:
            raise RuntimeError(
                "SharePoint browser is not configured."
            )

        return self._browse_sharepoint

    async def list_sharepoint_sites(self) -> list[BrowseNode]:
        return await self._sharepoint_browser().list_sites()

    async def list_sharepoint_drives(
        self,
        *,
        site_id: str,
    ) -> list[BrowseNode]:
        return await self._sharepoint_browser().list_drives(
            site_id=site_id,
        )

    async def list_sharepoint_drive_children(
        self,
        *,
        site_id: str,
        drive_id: str,
    ) -> list[BrowseNode]:
        return await self._sharepoint_browser().list_drive_children(
            site_id=site_id,
            drive_id=drive_id,
        )

    async def list_sharepoint_folder_children(
        self,
        *,
        site_id: str,
        drive_id: str,
        folder_id: str,
    ) -> list[BrowseNode]:
        return await self._sharepoint_browser().list_folder_children(
            site_id=site_id,
            drive_id=drive_id,
            folder_id=folder_id,
        )
