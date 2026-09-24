from __future__ import annotations

from ..domain.configuration import DropboxConfiguration
from ..domain.contracts.client import DropboxClient
from ..domain.entities.browse_node import DropboxBrowseNode
from ..domain.entities.client_models import DropboxEntry


class DropboxBrowseProvider:
    def __init__(self, client: DropboxClient, configuration: DropboxConfiguration) -> None:
        self._client = client
        self._configuration = configuration

    async def list_root_children(self) -> list[DropboxBrowseNode]:
        return await self.list_folder_children(self._configuration.root_path)

    async def list_folder_children(self, path: str) -> list[DropboxBrowseNode]:
        resolved_path = self._configuration.resolve_path(path)
        page = await self._client.list_folder(resolved_path, recursive=False)
        entries = list(page.entries)
        while page.has_more:
            if not page.cursor:
                raise RuntimeError("Dropbox returned has_more without a cursor.")
            page = await self._client.list_folder_continue(page.cursor)
            entries.extend(page.entries)
        return [self._to_node(entry, resolved_path) for entry in entries if entry.kind != "deleted"]

    @staticmethod
    def _to_node(entry: DropboxEntry, parent_path: str) -> DropboxBrowseNode:
        return DropboxBrowseNode(
            id=entry.id,
            name=entry.name,
            type=entry.kind,
            path_lower=entry.path_lower,
            path_display=entry.path_display,
            parent_path=parent_path,
            has_children=entry.kind == "folder",
        )
