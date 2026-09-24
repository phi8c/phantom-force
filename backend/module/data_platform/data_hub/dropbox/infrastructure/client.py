from __future__ import annotations

import asyncio
from typing import Any

from ..domain.configuration import DropboxConfiguration
from ..domain.entities.client_models import DropboxEntry, DropboxListPage


class DropboxSdkClient:
    """Async boundary around the blocking official Dropbox Python SDK."""

    def __init__(self, configuration: DropboxConfiguration) -> None:
        try:
            import dropbox
        except ImportError as exc:
            raise RuntimeError(
                "Dropbox SDK is not installed. Add dependency 'dropbox>=12.0.2,<13'."
            ) from exc

        self._sdk = dropbox.Dropbox(
            oauth2_refresh_token=configuration.refresh_token,
            app_key=configuration.app_key,
            app_secret=configuration.app_secret,
        )

    async def list_folder(self, path: str, *, recursive: bool) -> DropboxListPage:
        result = await asyncio.to_thread(
            self._sdk.files_list_folder,
            path,
            recursive=recursive,
        )
        return self._to_page(result)

    async def list_folder_continue(self, cursor: str) -> DropboxListPage:
        result = await asyncio.to_thread(self._sdk.files_list_folder_continue, cursor)
        return self._to_page(result)

    async def download(self, identity: str) -> bytes:
        _, response = await asyncio.to_thread(self._sdk.files_download, identity)
        return bytes(response.content)

    @classmethod
    def _to_page(cls, result: Any) -> DropboxListPage:
        return DropboxListPage(
            entries=[cls._to_entry(entry) for entry in result.entries],
            cursor=getattr(result, "cursor", None),
            has_more=bool(getattr(result, "has_more", False)),
        )

    @staticmethod
    def _to_entry(entry: Any) -> DropboxEntry:
        class_name = type(entry).__name__
        if class_name == "FileMetadata":
            kind = "file"
        elif class_name == "FolderMetadata":
            kind = "folder"
        else:
            kind = "deleted"
        return DropboxEntry(
            kind=kind,
            id=str(getattr(entry, "id", "")),
            name=str(getattr(entry, "name", "")),
            path_lower=getattr(entry, "path_lower", None),
            path_display=getattr(entry, "path_display", None),
            size=getattr(entry, "size", None),
            client_modified=getattr(entry, "client_modified", None),
            server_modified=getattr(entry, "server_modified", None),
            rev=getattr(entry, "rev", None),
            content_hash=getattr(entry, "content_hash", None),
        )
