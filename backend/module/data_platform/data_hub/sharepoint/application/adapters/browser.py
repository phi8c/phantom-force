from __future__ import annotations

from typing import Any, Mapping

from module.data_platform.common.microsoft_graph.client import MicrosoftGraphClient
from module.data_platform.data_hub.shared.domain.contracts.browser import (
    DataHubBrowser,
    InvalidBrowseLocatorError,
)
from module.data_platform.data_hub.shared.domain.entities.browse_node import (
    DataHubBrowseNode,
)
from module.data_platform.data_hub.sharepoint.domain.entities.browse_node import (
    BrowseNode,
)
from module.data_platform.data_hub.sharepoint.infrastructure.browser import (
    SharePointBrowseProvider,
)


class SharePointBrowserAdapter(DataHubBrowser):
    PROVIDER = "sharepoint"

    def __init__(
        self,
        browser: SharePointBrowseProvider,
        graph_client: MicrosoftGraphClient | None = None,
    ) -> None:
        self._browser = browser
        self._graph_client = graph_client

    async def browse_root(self) -> list[DataHubBrowseNode]:
        return [self._site(node) for node in await self._browser.list_sites()]

    async def browse_children(
        self,
        locator: Mapping[str, Any],
    ) -> list[DataHubBrowseNode]:
        self._reject_foreign_locator(locator)
        kind = locator.get("kind")
        site_id = self._string(locator, "site_id")
        if kind == "site" or (kind is None and "drive_id" not in locator):
            return [
                self._drive(node)
                for node in await self._browser.list_drives(site_id=site_id)
            ]

        drive_id = self._string(locator, "drive_id")
        if kind == "drive" or (kind is None and "item_id" not in locator):
            nodes = await self._browser.list_drive_children(
                site_id=site_id,
                drive_id=drive_id,
            )
        elif kind in {"folder", None}:
            nodes = await self._browser.list_folder_children(
                site_id=site_id,
                drive_id=drive_id,
                folder_id=self._string(locator, "item_id"),
            )
        else:
            raise InvalidBrowseLocatorError(
                f"SharePoint locator kind '{kind}' cannot be browsed."
            )
        return [self._item(node) for node in nodes]

    async def close(self) -> None:
        if self._graph_client is not None:
            await self._graph_client.close()

    def _site(self, node: BrowseNode) -> DataHubBrowseNode:
        return self._node(node, {"kind": "site", "site_id": node.id})

    def _drive(self, node: BrowseNode) -> DataHubBrowseNode:
        return self._node(
            node,
            {"kind": "drive", "site_id": node.site_id, "drive_id": node.id},
        )

    def _item(self, node: BrowseNode) -> DataHubBrowseNode:
        return self._node(
            node,
            {
                "kind": node.type,
                "site_id": node.site_id,
                "drive_id": node.drive_id,
                "item_id": node.id,
            },
        )

    def _node(
        self,
        node: BrowseNode,
        locator: Mapping[str, Any],
    ) -> DataHubBrowseNode:
        return DataHubBrowseNode(
            id=node.id,
            name=node.name,
            type=node.type,
            has_children=node.has_children,
            provider=self.PROVIDER,
            locator=dict(locator),
        )

    @staticmethod
    def _string(locator: Mapping[str, Any], key: str) -> str:
        value = locator.get(key)
        if not isinstance(value, str) or not value.strip():
            raise InvalidBrowseLocatorError(
                f"SharePoint locator requires non-empty '{key}'."
            )
        return value.strip()

    @staticmethod
    def _reject_foreign_locator(locator: Mapping[str, Any]) -> None:
        if not isinstance(locator, Mapping):
            raise InvalidBrowseLocatorError("SharePoint locator must be an object.")
        if "path" in locator:
            raise InvalidBrowseLocatorError(
                "Dropbox locator is not valid for SharePoint."
            )
