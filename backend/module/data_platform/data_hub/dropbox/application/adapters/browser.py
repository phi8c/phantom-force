from __future__ import annotations

from typing import Any, Mapping

from module.data_platform.data_hub.shared.domain.contracts.browser import (
    DataHubBrowser,
    InvalidBrowseLocatorError,
)
from module.data_platform.data_hub.shared.domain.entities.browse_node import (
    DataHubBrowseNode,
)
from module.data_platform.data_hub.dropbox.domain.entities.browse_node import (
    DropboxBrowseNode,
)
from module.data_platform.data_hub.dropbox.infrastructure.browser import (
    DropboxBrowseProvider,
)
from module.data_platform.data_hub.dropbox.infrastructure.client import DropboxHttpClient


class DropboxBrowserAdapter(DataHubBrowser):
    PROVIDER = "dropbox"

    def __init__(
        self,
        browser: DropboxBrowseProvider,
        client: DropboxHttpClient | None = None,
    ) -> None:
        self._browser = browser
        self._client = client

    async def browse_root(self) -> list[DataHubBrowseNode]:
        return [self._node(node) for node in await self._browser.list_root_children()]

    async def browse_children(
        self,
        locator: Mapping[str, Any],
    ) -> list[DataHubBrowseNode]:
        if not isinstance(locator, Mapping):
            raise InvalidBrowseLocatorError("Dropbox locator must be an object.")
        if any(key in locator for key in ("site_id", "drive_id", "item_id")):
            raise InvalidBrowseLocatorError(
                "SharePoint locator is not valid for Dropbox."
            )
        path = locator.get("path")
        if not isinstance(path, str) or not path.strip():
            raise InvalidBrowseLocatorError(
                "Dropbox locator requires non-empty 'path'."
            )
        nodes = await self._browser.list_folder_children(path.strip())
        return [self._node(node) for node in nodes]

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()

    def _node(self, node: DropboxBrowseNode) -> DataHubBrowseNode:
        path = node.path_lower or node.path_display
        if not path:
            raise ValueError("Dropbox browse entry has no path.")
        return DataHubBrowseNode(
            id=node.id,
            name=node.name,
            type=node.type,
            has_children=node.has_children,
            provider=self.PROVIDER,
            locator={"path": path},
        )
