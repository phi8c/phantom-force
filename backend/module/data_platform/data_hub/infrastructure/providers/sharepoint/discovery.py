from __future__ import annotations

from datetime import datetime
from typing import Any

from module.data_platform.common.microsoft_graph.client import (
    MicrosoftGraphClient,
)
from module.data_platform.data_hub.domain.contracts.discovery_provider import (
    DiscoveryProvider,
)
from module.data_platform.data_hub.domain.entities.discovered_file import (
    DiscoveredFile,
)
from module.data_platform.data_hub.domain.entities.discovery_page import (
    DiscoveryPage,
)
from module.data_platform.data_hub.domain.value_objects.source_reference import (
    SourceReference,
)


class SharePointDiscoveryProvider(
    DiscoveryProvider,
):
    """
    Paged and resumable SharePoint discovery.

    Cursor contains only traversal state:
    - current_page_url
    - item_offset
    - pending_endpoints

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

        site_id = self._get_required_metadata(
            source,
            "site_id",
        )

        drive_id = self._get_required_metadata(
            source,
            "drive_id",
        )

        folder_id = source.metadata.get(
            "folder_id"
        )

        # ---------------------------------------------
        # Restore or initialize traversal state
        # ---------------------------------------------

        if cursor:
            pending_endpoints = list(
                cursor.get(
                    "pending_endpoints",
                    [],
                )
            )

            current_page_url = cursor.get(
                "current_page_url"
            )

            item_offset = int(
                cursor.get(
                    "item_offset",
                    0,
                )
            )

        else:
            pending_endpoints = [
                self._children_endpoint(
                    site_id=site_id,
                    drive_id=drive_id,
                    folder_id=folder_id,
                )
            ]

            current_page_url = None
            item_offset = 0

        discovered_files: list[
            DiscoveredFile
        ] = []

        # ---------------------------------------------
        # Process until batch is full or traversal ends
        # ---------------------------------------------

        while len(discovered_files) < limit:

            if current_page_url is None:

                if not pending_endpoints:
                    break

                current_page_url = (
                    pending_endpoints.pop()
                )

                item_offset = 0

            response = await self._graph_client.get(
                current_page_url
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
                                site_id=site_id,
                                drive_id=drive_id,
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
                    site_id=site_id,
                    drive_id=drive_id,
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
                            "current_page_url": (
                                current_page_url
                            ),
                            "item_offset": index,
                            "pending_endpoints": (
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
                            "current_page_url": (
                                next_link
                            ),
                            "item_offset": 0,
                            "pending_endpoints": (
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

            current_page_url = response.get(
                "@odata.nextLink"
            )

            item_offset = 0

        # ---------------------------------------------
        # Traversal finished
        # ---------------------------------------------

        has_more = bool(
            current_page_url
            or pending_endpoints
        )

        next_cursor = None

        if has_more:
            next_cursor = {
                "current_page_url": (
                    current_page_url
                ),
                "item_offset": item_offset,
                "pending_endpoints": (
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
    ) -> str:

        if folder_id:
            return (
                f"/sites/{site_id}"
                f"/drives/{drive_id}"
                f"/items/{folder_id}"
                f"/children"
            )

        return (
            f"/sites/{site_id}"
            f"/drives/{drive_id}"
            f"/root/children"
        )

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
            "site_id": source.metadata.get(
                "site_id"
            ),
            "drive_id": source.metadata.get(
                "drive_id"
            ),
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

        cls._get_required_metadata(
            source,
            "site_id",
        )

        cls._get_required_metadata(
            source,
            "drive_id",
        )

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
