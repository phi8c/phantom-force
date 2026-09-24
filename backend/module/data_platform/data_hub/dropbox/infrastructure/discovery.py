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

        source_paths = self._source_paths(source)
        (
            root_index,
            pending,
            sdk_cursor,
            sdk_has_more,
            started,
            seen_file_ids,
        ) = self._restore_cursor(
            cursor,
            source_paths,
        )
        items: list[DiscoveredFile] = []

        while len(items) < limit:
            while pending and len(items) < limit:
                record = pending.pop(0)
                file_id = str(record["id"])
                if file_id in seen_file_ids:
                    continue
                seen_file_ids.add(file_id)
                items.append(self._record_to_file(record, source))
            if len(items) >= limit:
                break

            if root_index >= len(source_paths):
                break

            if not started:
                page = await self._client.list_folder(
                    source_paths[root_index],
                    recursive=True,
                )
                started = True
            elif sdk_has_more:
                if not sdk_cursor:
                    raise RuntimeError("Dropbox returned has_more without a cursor.")
                page = await self._client.list_folder_continue(sdk_cursor)
            else:
                root_index += 1
                sdk_cursor = None
                sdk_has_more = False
                started = False
                continue

            pending.extend(
                self._entry_to_record(entry)
                for entry in page.entries
                if entry.kind == "file"
            )
            sdk_cursor = page.cursor
            sdk_has_more = page.has_more

        has_more = bool(
            pending
            or sdk_has_more
            or root_index < len(source_paths) - 1
        )
        next_cursor = None
        if has_more:
            next_cursor = {
                "source_paths": source_paths,
                "root_index": root_index,
                "dropbox_cursor": sdk_cursor,
                "dropbox_has_more": sdk_has_more,
                "pending_files": pending,
                "started": started,
                "seen_file_ids": sorted(seen_file_ids),
            }
        return DiscoveryPage(items=items, next_cursor=next_cursor, has_more=has_more)

    def _restore_cursor(
        self,
        cursor: dict[str, Any] | None,
        source_paths: list[str],
    ) -> tuple[int, list[dict[str, Any]], str | None, bool, bool, set[str]]:
        if cursor is None:
            return 0, [], None, False, False, set()
        cursor_paths = cursor.get("source_paths")
        if cursor_paths is None and cursor.get("source_path") is not None:
            cursor_paths = [cursor.get("source_path")]
        if cursor_paths != source_paths:
            raise ValueError("Dropbox discovery cursor does not belong to this source.")
        root_index = cursor.get("root_index", 0)
        if not isinstance(root_index, int) or not 0 <= root_index < len(source_paths):
            raise ValueError("Dropbox discovery cursor has an invalid root_index.")
        pending = cursor.get("pending_files", [])
        if not isinstance(pending, list) or not all(isinstance(item, dict) for item in pending):
            raise ValueError("Dropbox discovery cursor has invalid pending_files.")
        sdk_cursor = cursor.get("dropbox_cursor")
        if sdk_cursor is not None and not isinstance(sdk_cursor, str):
            raise ValueError("Dropbox discovery cursor has an invalid Dropbox cursor.")
        seen_file_ids = cursor.get("seen_file_ids", [])
        if not isinstance(seen_file_ids, list) or not all(
            isinstance(item, str) for item in seen_file_ids
        ):
            raise ValueError("Dropbox discovery cursor has invalid seen_file_ids.")
        return (
            root_index,
            list(pending),
            sdk_cursor,
            bool(cursor.get("dropbox_has_more", False)),
            bool(cursor.get("started", True)),
            set(seen_file_ids),
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

    def _source_paths(self, source: SourceReference) -> list[str]:
        roots = source.metadata.get("roots")
        if roots is None:
            return [self._configuration.resolve_path(self._configuration.root_path)]
        if not isinstance(roots, list) or not roots:
            raise ValueError("Dropbox discovery roots must be a non-empty list.")

        paths: list[str] = []
        for root in roots:
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
            paths.append(self._configuration.resolve_path(path))
        return paths
