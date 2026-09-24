from __future__ import annotations

from datetime import datetime
from typing import Any

from module.data_platform.common.microsoft_graph.client import (
    MicrosoftGraphClient,
)
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


class SharePointDiscoveryProvider(
    DiscoveryProvider,
):
    """
    Paged and resumable SharePoint discovery.

    Cursor contains traversal state with SharePoint source context:
    - current.site_id
    - current.drive_id
    - current.url
    - item_offset
    - pending

    SharePoint-specific concepts stay inside this provider.
    """

    PROVIDER_NAME = "sharepoint"
    INGESTED_FIELD_NAME = "DaIngest"

    def __init__(
        self,
        graph_client: MicrosoftGraphClient,
    ) -> None:
        self._graph_client = graph_client

    async def discover(
        self,
        source: SourceReference,
        *,
        cursor: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> DiscoveryPage:

        self._validate_source(source)

        if limit <= 0:
            raise ValueError(
                "Discovery limit must be greater than 0"
            )

        # ---------------------------------------------
        # Restore or initialize traversal state
        # ---------------------------------------------

        if cursor:
            pending_endpoints = self._restore_pending(
                cursor,
                source,
            )
            current_endpoint = self._restore_current(
                cursor,
                source,
            )
            item_offset = int(
                cursor.get(
                    "item_offset",
                    0,
                )
            )

        else:
            pending_endpoints = [
                self._to_endpoint_context(
                    root
                )
                for root in self._source_roots(source)
            ]

            current_endpoint = None
            item_offset = 0

        discovered_files: list[
            DiscoveredFile
        ] = []

        # ---------------------------------------------
        # Process until batch is full or traversal ends
        # ---------------------------------------------

        while len(discovered_files) < limit:

            if current_endpoint is None:

                if not pending_endpoints:
                    break

                current_endpoint = (
                    pending_endpoints.pop()
                )

                item_offset = 0

            response = await self._graph_client.get(
                current_endpoint["url"]
            )

            values = response.get(
                "value",
                [],
            )

            index = item_offset

            while index < len(values):

                item = values[index]

                # Important:
                # offset points to NEXT unprocessed item.
                index += 1

                # -------------------------------------
                # Folder
                # -------------------------------------

                if self._is_folder(item):

                    child_folder_id = item.get(
                        "id"
                    )

                    if child_folder_id:

                        pending_endpoints.append(
                            self._children_endpoint(
                                site_id=current_endpoint[
                                    "site_id"
                                ],
                                drive_id=current_endpoint[
                                    "drive_id"
                                ],
                                folder_id=child_folder_id,
                            )
                        )

                    continue

                # -------------------------------------
                # File
                # -------------------------------------

                if not self._is_file(item):
                    continue

                sharepoint_fields = await self._drive_item_fields(
                    site_id=current_endpoint["site_id"],
                    drive_id=current_endpoint["drive_id"],
                    item_id=str(item["id"]),
                )
                if self._is_already_ingested(
                    sharepoint_fields,
                ):
                    continue

                discovered_files.append(
                    self._to_discovered_file(
                        item=item,
                        source=source,
                        site_id=current_endpoint["site_id"],
                        drive_id=current_endpoint["drive_id"],
                        sharepoint_fields=sharepoint_fields,
                    )
                )

                # -------------------------------------
                # Batch full
                # -------------------------------------

                if (
                    len(discovered_files)
                    >= limit
                ):

                    # Still have unprocessed items
                    # inside current Graph page.
                    if index < len(values):

                        next_cursor = {
                            "current": (
                                current_endpoint
                            ),
                            "item_offset": index,
                            "pending": (
                                pending_endpoints
                            ),
                        }

                        return DiscoveryPage(
                            items=discovered_files,
                            next_cursor=next_cursor,
                            has_more=True,
                        )

                    # Current Graph page finished.
                    next_link = response.get(
                        "@odata.nextLink"
                    )

                    if (
                        next_link
                        or pending_endpoints
                    ):

                        next_cursor = {
                            "current": (
                                self._with_url(
                                    current_endpoint,
                                    next_link,
                                )
                                if next_link
                                else None
                            ),
                            "item_offset": 0,
                            "pending": (
                                pending_endpoints
                            ),
                        }

                        return DiscoveryPage(
                            items=discovered_files,
                            next_cursor=next_cursor,
                            has_more=True,
                        )

                    return DiscoveryPage(
                        items=discovered_files,
                        next_cursor=None,
                        has_more=False,
                    )

            # -----------------------------------------
            # Current Graph page fully processed
            # -----------------------------------------

            next_link = response.get(
                "@odata.nextLink"
            )
            current_endpoint = (
                self._with_url(
                    current_endpoint,
                    next_link,
                )
                if next_link
                else None
            )

            item_offset = 0

        # ---------------------------------------------
        # Traversal finished
        # ---------------------------------------------

        has_more = bool(
            current_endpoint
            or pending_endpoints
        )

        next_cursor = None

        if has_more:
            next_cursor = {
                "current": (
                    current_endpoint
                ),
                "item_offset": item_offset,
                "pending": (
                    pending_endpoints
                ),
            }

        return DiscoveryPage(
            items=discovered_files,
            next_cursor=next_cursor,
            has_more=has_more,
        )

    @staticmethod
    def _children_endpoint(
        *,
        site_id: str,
        drive_id: str,
        folder_id: str | None,
    ) -> dict[str, str]:

        if folder_id:
            url = (
                f"/sites/{site_id}"
                f"/drives/{drive_id}"
                f"/items/{folder_id}"
                f"/children"
            )
        else:
            url = (
                f"/sites/{site_id}"
                f"/drives/{drive_id}"
                f"/root/children"
            )

        return {
            "site_id": site_id,
            "drive_id": drive_id,
            "url": url,
        }

    @staticmethod
    def _list_item_endpoint(
        *,
        site_id: str,
        drive_id: str,
        item_id: str,
    ) -> str:

        return (
            f"/sites/{site_id}"
            f"/drives/{drive_id}"
            f"/items/{item_id}"
            f"/listItem"
        )

    async def _drive_item_fields(
        self,
        *,
        site_id: str,
        drive_id: str,
        item_id: str,
    ) -> dict[str, Any]:

        list_item = await self._graph_client.get(
            self._list_item_endpoint(
                site_id=site_id,
                drive_id=drive_id,
                item_id=item_id,
            ),
            params={
                "$expand": "fields",
            },
        )

        fields = (
            list_item.get("fields")
            or {}
        )
        if not isinstance(fields, dict):
            return {}
        return fields

    @classmethod
    def _is_already_ingested(
        cls,
        fields: dict[str, Any],
    ) -> bool:

        value = fields.get(
            cls.INGESTED_FIELD_NAME
        )
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {
                "true",
                "1",
                "yes",
            }
        return False

    @staticmethod
    def _is_folder(
        item: dict[str, Any],
    ) -> bool:
        return (
            item.get("folder")
            is not None
        )

    @staticmethod
    def _is_file(
        item: dict[str, Any],
    ) -> bool:
        return (
            item.get("file")
            is not None
        )

    @classmethod
    def _to_discovered_file(
        cls,
        *,
        item: dict[str, Any],
        source: SourceReference,
        site_id: str,
        drive_id: str,
        sharepoint_fields: dict[str, Any] | None = None,
    ) -> DiscoveredFile:

        name = item.get(
            "name",
            "",
        )

        file_metadata = (
            item.get("file")
            or {}
        )

        last_modified_at = (
            cls._parse_datetime(
                item.get(
                    "lastModifiedDateTime"
                )
            )
        )

        parent_reference = (
            item.get("parentReference")
            or {}
        )

        provider_metadata = {
            "site_id": site_id,
            "drive_id": drive_id,
            "item_id": item.get(
                "id"
            ),
            "parent_id": (
                parent_reference.get(
                    "id"
                )
            ),
            "drive_item": item,
            "mime_type": (
                file_metadata.get(
                    "mimeType"
                )
            ),
            "sharepoint_fields": (
                sharepoint_fields
                or {}
            ),
        }

        return DiscoveredFile(
            external_file_id=item["id"],
            file_name=name,
            file_extension=(
                cls._extract_extension(
                    name
                )
            ),
            file_size_bytes=(
                item.get("size")
            ),
            source_file_url=(
                item.get("webUrl")
            ),
            source=source,
            provider_metadata=(
                provider_metadata
            ),
            last_modified_at=(
                last_modified_at
            ),
            original_file_path=(
                cls._build_path(
                    item
                )
            ),
        )

    @staticmethod
    def _build_path(
        item: dict[str, Any],
    ) -> str | None:

        parent_reference = (
            item.get("parentReference")
            or {}
        )

        parent_path = (
            parent_reference.get(
                "path"
            )
        )

        if not parent_path:
            return item.get(
                "name"
            )

        if ":/" in parent_path:
            parent_path = (
                parent_path.split(
                    ":/",
                    1,
                )[1]
            )

        return (
            f"{parent_path.rstrip('/')}/"
            f"{item.get('name', '')}"
        )

    @staticmethod
    def _extract_extension(
        file_name: str,
    ) -> str | None:

        if "." not in file_name:
            return None

        return (
            file_name.rsplit(
                ".",
                1,
            )[1].lower()
        )

    @staticmethod
    def _parse_datetime(
        value: str | None,
    ) -> datetime | None:

        if not value:
            return None

        return datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )

    @classmethod
    def _validate_source(
        cls,
        source: SourceReference,
    ) -> None:

        if (
            source.provider
            != cls.PROVIDER_NAME
        ):
            raise ValueError(
                f"Unsupported provider: "
                f"{source.provider}"
            )

        cls._source_roots(source)

    @classmethod
    def _source_roots(
        cls,
        source: SourceReference,
    ) -> list[dict[str, str | None]]:
        roots = source.metadata.get("roots")
        if roots is None:
            return [
                {
                    "site_id": cls._get_required_metadata(
                        source,
                        "site_id",
                    ),
                    "drive_id": cls._get_required_metadata(
                        source,
                        "drive_id",
                    ),
                    "folder_id": (
                        str(source.metadata.get("folder_id"))
                        if source.metadata.get("folder_id")
                        else None
                    ),
                }
            ]

        if not isinstance(roots, list) or not roots:
            raise ValueError(
                "SharePoint source metadata.roots must be a non-empty list"
            )

        normalized_roots: list[dict[str, str | None]] = []

        for root in roots:
            if not isinstance(root, dict):
                raise ValueError(
                    "SharePoint source metadata.roots items must be objects"
                )

            locator = root.get("locator", root)
            if not isinstance(locator, dict):
                raise ValueError(
                    "SharePoint source metadata root locator must be an object"
                )
            if "path" in locator:
                raise ValueError("Dropbox locator is not valid for SharePoint discovery")

            site_id = cls._get_required_root_value(
                locator,
                "site_id",
            )
            drive_id = cls._get_required_root_value(
                locator,
                "drive_id",
            )
            folder_value = locator.get("folder_id") or locator.get("item_id")
            folder_id = (
                str(folder_value)
                if folder_value
                else None
            )

            normalized_roots.append(
                {
                    "site_id": site_id,
                    "drive_id": drive_id,
                    "folder_id": folder_id,
                }
            )

        return normalized_roots

    @classmethod
    def _to_endpoint_context(
        cls,
        root: dict[str, str | None],
    ) -> dict[str, str]:
        site_id = cls._require_context_value(
            root.get("site_id"),
            "site_id",
        )
        drive_id = cls._require_context_value(
            root.get("drive_id"),
            "drive_id",
        )

        return cls._children_endpoint(
            site_id=site_id,
            drive_id=drive_id,
            folder_id=root.get("folder_id"),
        )

    @classmethod
    def _restore_current(
        cls,
        cursor: dict[str, Any],
        source: SourceReference,
    ) -> dict[str, str] | None:
        current = cursor.get("current")
        if isinstance(current, dict):
            return cls._normalize_endpoint_context(current)

        current_page_url = cursor.get("current_page_url")
        if not current_page_url:
            return None

        return {
            "site_id": cls._require_context_value(
                cursor.get("site_id")
                or source.metadata.get("site_id"),
                "site_id",
            ),
            "drive_id": cls._require_context_value(
                cursor.get("drive_id")
                or source.metadata.get("drive_id"),
                "drive_id",
            ),
            "url": str(current_page_url),
        }

    @classmethod
    def _restore_pending(
        cls,
        cursor: dict[str, Any],
        source: SourceReference,
    ) -> list[dict[str, str]]:
        pending = cursor.get("pending")
        if isinstance(pending, list):
            return [
                cls._normalize_endpoint_context(endpoint)
                for endpoint in pending
                if isinstance(endpoint, dict)
            ]

        legacy_pending = cursor.get(
            "pending_endpoints",
            [],
        )
        if not isinstance(legacy_pending, list):
            return []

        site_id = cls._require_context_value(
            cursor.get("site_id")
            or source.metadata.get("site_id"),
            "site_id",
        )
        drive_id = cls._require_context_value(
            cursor.get("drive_id")
            or source.metadata.get("drive_id"),
            "drive_id",
        )

        return [
            {
                "site_id": site_id,
                "drive_id": drive_id,
                "url": str(endpoint),
            }
            for endpoint in legacy_pending
            if endpoint
        ]

    @classmethod
    def _normalize_endpoint_context(
        cls,
        endpoint: dict[str, Any],
    ) -> dict[str, str]:
        return {
            "site_id": cls._require_context_value(
                endpoint.get("site_id"),
                "site_id",
            ),
            "drive_id": cls._require_context_value(
                endpoint.get("drive_id"),
                "drive_id",
            ),
            "url": cls._require_context_value(
                endpoint.get("url"),
                "url",
            ),
        }

    @staticmethod
    def _with_url(
        endpoint: dict[str, str],
        url: str,
    ) -> dict[str, str]:
        return {
            "site_id": endpoint["site_id"],
            "drive_id": endpoint["drive_id"],
            "url": url,
        }

    @staticmethod
    def _get_required_root_value(
        root: dict[str, Any],
        key: str,
    ) -> str:
        return SharePointDiscoveryProvider._require_context_value(
            root.get(key),
            key,
        )

    @staticmethod
    def _require_context_value(
        value: Any,
        key: str,
    ) -> str:
        if value is None or str(value).strip() == "":
            raise ValueError(
                f"Missing SharePoint source metadata: {key}"
            )

        return str(value)

    @staticmethod
    def _get_required_metadata(
        source: SourceReference,
        key: str,
    ) -> str:

        value = source.metadata.get(
            key
        )

        if not value:
            raise ValueError(
                f"Missing SharePoint source "
                f"metadata: {key}"
            )

        return str(value)
