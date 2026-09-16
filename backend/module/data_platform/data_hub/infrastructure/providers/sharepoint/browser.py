from __future__ import annotations

from typing import Any

from module.data_platform.common.microsoft_graph.client import (
    MicrosoftGraphClient,
)
from module.data_platform.data_hub.domain.contracts.browse_provider import (
    BrowseProvider,
)
from module.data_platform.data_hub.domain.entities.browse_node import (
    BrowseNode,
)


class SharePointBrowseProvider(BrowseProvider):
    def __init__(
        self,
        graph_client: MicrosoftGraphClient,
    ) -> None:
        self._graph_client = graph_client

    async def list_sites(self) -> list[BrowseNode]:
        response = await self._graph_client.get(
            "/sites",
            params={
                "search": "*",
                "$select": "id,name,displayName",
            },
        )

        return [
            BrowseNode(
                id=str(site["id"]),
                name=str(
                    site.get("displayName")
                    or site.get("name")
                    or site["id"]
                ),
                type="site",
                site_id=str(site["id"]),
                has_children=True,
            )
            for site in self._values(response)
            if site.get("id")
        ]

    async def list_drives(
        self,
        *,
        site_id: str,
    ) -> list[BrowseNode]:
        response = await self._graph_client.get(
            f"/sites/{site_id}/drives",
            params={
                "$select": "id,name,driveType",
            },
        )

        return [
            BrowseNode(
                id=str(drive["id"]),
                name=str(drive.get("name") or drive["id"]),
                type="drive",
                site_id=site_id,
                drive_id=str(drive["id"]),
                parent_id=site_id,
                has_children=True,
            )
            for drive in self._values(response)
            if drive.get("id")
        ]

    async def list_drive_children(
        self,
        *,
        site_id: str,
        drive_id: str,
    ) -> list[BrowseNode]:
        return await self._list_children(
            endpoint=(
                f"/sites/{site_id}"
                f"/drives/{drive_id}"
                f"/root/children"
            ),
            site_id=site_id,
            drive_id=drive_id,
            parent_id=drive_id,
        )

    async def list_folder_children(
        self,
        *,
        site_id: str,
        drive_id: str,
        folder_id: str,
    ) -> list[BrowseNode]:
        return await self._list_children(
            endpoint=(
                f"/sites/{site_id}"
                f"/drives/{drive_id}"
                f"/items/{folder_id}"
                f"/children"
            ),
            site_id=site_id,
            drive_id=drive_id,
            parent_id=folder_id,
        )

    async def _list_children(
        self,
        *,
        endpoint: str,
        site_id: str,
        drive_id: str,
        parent_id: str,
    ) -> list[BrowseNode]:
        response = await self._graph_client.get(
            endpoint,
            params={
                "$select": "id,name,folder,file,parentReference",
            },
        )

        return [
            self._to_child_node(
                item=item,
                site_id=site_id,
                drive_id=drive_id,
                parent_id=parent_id,
            )
            for item in self._values(response)
            if item.get("id")
        ]

    @staticmethod
    def _to_child_node(
        *,
        item: dict[str, Any],
        site_id: str,
        drive_id: str,
        parent_id: str,
    ) -> BrowseNode:
        folder = item.get("folder")
        is_folder = isinstance(folder, dict)

        return BrowseNode(
            id=str(item["id"]),
            name=str(item.get("name") or item["id"]),
            type="folder" if is_folder else "file",
            site_id=site_id,
            drive_id=drive_id,
            parent_id=parent_id,
            has_children=(
                is_folder
                and int(folder.get("childCount") or 0) > 0
            ),
        )

    @staticmethod
    def _values(
        response: dict[str, Any],
    ) -> list[dict[str, Any]]:
        values = response.get("value", [])
        if not isinstance(values, list):
            return []

        return [
            value
            for value in values
            if isinstance(value, dict)
        ]
