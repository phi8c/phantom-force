from __future__ import annotations

from module.data_platform.data_hub.domain.contracts.browse_provider import (
    BrowseProvider,
)
from module.data_platform.data_hub.domain.entities.browse_node import (
    BrowseNode,
)


class BrowseSharePointUseCase:
    def __init__(
        self,
        browse_provider: BrowseProvider,
    ) -> None:
        self._browse_provider = browse_provider

    async def list_sites(self) -> list[BrowseNode]:
        return await self._browse_provider.list_sites()

    async def list_drives(
        self,
        *,
        site_id: str,
    ) -> list[BrowseNode]:
        return await self._browse_provider.list_drives(
            site_id=site_id,
        )

    async def list_drive_children(
        self,
        *,
        site_id: str,
        drive_id: str,
    ) -> list[BrowseNode]:
        return await self._browse_provider.list_drive_children(
            site_id=site_id,
            drive_id=drive_id,
        )

    async def list_folder_children(
        self,
        *,
        site_id: str,
        drive_id: str,
        folder_id: str,
    ) -> list[BrowseNode]:
        return await self._browse_provider.list_folder_children(
            site_id=site_id,
            drive_id=drive_id,
            folder_id=folder_id,
        )
