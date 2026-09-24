from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from module.data_platform.data_hub.sharepoint.domain.entities.browse_node import (
    BrowseNode,
)


class BrowseProvider(ABC):
    @abstractmethod
    async def list_sites(self) -> list[BrowseNode]:
        raise NotImplementedError

    @abstractmethod
    async def list_drives(
        self,
        *,
        site_id: str,
    ) -> list[BrowseNode]:
        raise NotImplementedError

    @abstractmethod
    async def list_drive_children(
        self,
        *,
        site_id: str,
        drive_id: str,
    ) -> list[BrowseNode]:
        raise NotImplementedError

    @abstractmethod
    async def list_folder_children(
        self,
        *,
        site_id: str,
        drive_id: str,
        folder_id: str,
    ) -> list[BrowseNode]:
        raise NotImplementedError
