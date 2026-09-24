from __future__ import annotations

from datetime import datetime
from typing import Any

from module.data_platform.data_hub.shared.domain.contracts.discovery_provider import (
    DiscoveryProvider,
)
from module.data_platform.data_hub.shared.domain.entities.discovered_file import (
    DiscoveredFile,
)
from module.data_platform.data_hub.shared.domain.entities.discovery_page import (
    DiscoveryPage,
)
from module.data_platform.data_hub.shared.domain.value_objects.source_reference import (
    SourceReference,
)

from ..domain.configuration import DropboxConfiguration
from ..domain.contracts.client import DropboxClient
from ..domain.entities.client_models import DropboxEntry


class DropboxDiscoveryProvider(DiscoveryProvider):
    PROVIDER_NAME = "dropbox"

    def __init__(self, client: DropboxClient, configuration: DropboxConfiguration) -> None:
        self._client = client
        self._configuration = configuration

    async def discover(
        self,
        source: SourceReference,
        *,
        cursor: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> DiscoveryPage:
        self._validate_source(source)
        if limit <= 0:
            raise ValueError("Discovery limit must be greater than 0.")

        source_path = self._source_path(source)
        pending, sdk_cursor, sdk_has_more, started = self._restore_cursor(
            cursor,
            source_path,
        )
        items: list[DiscoveredFile] = []

        while len(items) < limit:
            while pending and len(items) < limit:
                items.append(self._record_to_file(pending.pop(0), source))
            if len(items) >= limit:
                break

            if not started:
                page = await self._client.list_folder(source_path, recursive=True)
                started = True
            elif sdk_has_more:
                if not sdk_cursor:
                    raise RuntimeError("Dropbox returned has_more without a cursor.")
                page = await self._client.list_folder_continue(sdk_cursor)
            else:
                break

            pending.extend(
                self._entry_to_record(entry)
                for entry in page.entries
                if entry.kind == "file"
            )
            sdk_cursor = page.cursor
            sdk_has_more = page.has_more

        has_more = bool(pending or sdk_has_more)
        next_cursor = None
        if has_more:
            next_cursor = {
                "source_path": source_path,
                "dropbox_cursor": sdk_cursor,
                "dropbox_has_more": sdk_has_more,
                "pending_files": pending,
                "started": started,
            }
        return DiscoveryPage(items=items, next_cursor=next_cursor, has_more=has_more)

    def _restore_cursor(
        self,
        cursor: dict[str, Any] | None,
        source_path: str,
    ) -> tuple[list[dict[str, Any]], str | None, bool, bool]:
        if cursor is None:
            return [], None, False, False
        if cursor.get("source_path") != source_path:
            raise ValueError("Dropbox discovery cursor does not belong to this source.")
        pending = cursor.get("pending_files", [])
        if not isinstance(pending, list) or not all(isinstance(item, dict) for item in pending):
            raise ValueError("Dropbox discovery cursor has invalid pending_files.")
        sdk_cursor = cursor.get("dropbox_cursor")
        if sdk_cursor is not None and not isinstance(sdk_cursor, str):
            raise ValueError("Dropbox discovery cursor has an invalid Dropbox cursor.")
        return (
            list(pending),
            sdk_cursor,
            bool(cursor.get("dropbox_has_more", False)),
            bool(cursor.get("started", True)),
        )

    @classmethod
    def _entry_to_record(cls, entry: DropboxEntry) -> dict[str, Any]:
        return {
            "id": entry.id,
            "name": entry.name,
            "path_lower": entry.path_lower,
            "path_display": entry.path_display,
            "size": entry.size,
            "client_modified": cls._datetime_to_text(entry.client_modified),
            "server_modified": cls._datetime_to_text(entry.server_modified),
            "rev": entry.rev,
            "content_hash": entry.content_hash,
        }

    @classmethod
    def _record_to_file(
        cls,
        record: dict[str, Any],
        source: SourceReference,
    ) -> DiscoveredFile:
        metadata = {
            key: record[key]
            for key in ("id", "path_lower", "path_display", "rev", "content_hash")
            if record.get(key) is not None
        }
        return DiscoveredFile(
            external_file_id=str(record["id"]),
            file_name=str(record["name"]),
            file_extension=cls._extract_extension(str(record["name"])),
            file_size_bytes=record.get("size"),
            source_file_url=None,
            source=source,
            provider_metadata=metadata,
            last_modified_at=cls._text_to_datetime(
                record.get("server_modified") or record.get("client_modified")
            ),
            original_file_path=record.get("path_display") or record.get("path_lower"),
        )

    @staticmethod
    def _extract_extension(file_name: str) -> str | None:
        return file_name.rsplit(".", 1)[1].lower() if "." in file_name else None

    @staticmethod
    def _datetime_to_text(value: datetime | None) -> str | None:
        return value.isoformat() if value is not None else None

    @staticmethod
    def _text_to_datetime(value: Any) -> datetime | None:
        return datetime.fromisoformat(value) if isinstance(value, str) and value else None

    @classmethod
    def _validate_source(cls, source: SourceReference) -> None:
        if source.provider.strip().lower() != cls.PROVIDER_NAME:
            raise ValueError(
                f"Dropbox discovery requires provider '{cls.PROVIDER_NAME}', got '{source.provider}'."
            )
        if not isinstance(source.identifier, str):
            raise ValueError("Dropbox source identifier must be a string.")

    def _source_path(self, source: SourceReference) -> str:
        roots = source.metadata.get("roots")
        if roots is None:
            return self._configuration.resolve_path(self._configuration.root_path)
        if not isinstance(roots, list) or len(roots) != 1:
            raise ValueError("Dropbox discovery requires exactly one selected root.")
        root = roots[0]
        if not isinstance(root, dict):
            raise ValueError("Dropbox selected root must be an object.")
        locator = root.get("locator", root)
        if not isinstance(locator, dict):
            raise ValueError("Dropbox root locator must be an object.")
        if any(key in locator for key in ("site_id", "drive_id", "item_id")):
            raise ValueError("SharePoint locator is not valid for Dropbox discovery.")
        path = locator.get("path")
        if not isinstance(path, str) or not path.strip():
            raise ValueError("Dropbox root locator requires non-empty 'path'.")
        return self._configuration.resolve_path(path)
