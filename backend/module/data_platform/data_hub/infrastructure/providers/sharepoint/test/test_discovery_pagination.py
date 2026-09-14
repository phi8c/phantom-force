import pytest

from module.data_platform.data_hub.domain.value_objects.source_reference import (
    SourceReference,
)
from module.data_platform.data_hub.infrastructure.providers.sharepoint.discovery import (
    SharePointDiscoveryProvider,
)


@pytest.mark.asyncio
async def test_discovery_filters_da_ingest_true_and_keeps_false_or_missing():
    graph_client = FakeGraphClient(
        pages={
            "/sites/site/drives/drive/root/children": {
                "value": [
                    drive_file("file_true", "true.pdf"),
                    drive_file("file_false", "false.pdf"),
                    drive_file("file_missing", "missing.pdf"),
                ],
            },
        },
        fields={
            "file_true": {
                "DaIngest": True,
            },
            "file_false": {
                "DaIngest": False,
            },
        },
    )

    page = await SharePointDiscoveryProvider(graph_client).discover(
        source(),
        limit=10,
    )

    assert [
        item.external_file_id
        for item in page.items
    ] == [
        "file_false",
        "file_missing",
    ]
    assert page.items[0].provider_metadata["sharepoint_fields"] == {
        "DaIngest": False,
    }
    assert page.items[1].provider_metadata["sharepoint_fields"] == {}


@pytest.mark.asyncio
async def test_discovery_mixed_batch_returns_only_not_ingested_files():
    graph_client = FakeGraphClient(
        pages={
            "/sites/site/drives/drive/root/children": {
                "value": [
                    drive_file("file_1", "one.pdf"),
                    drive_file("file_2", "two.pdf"),
                    drive_file("file_3", "three.pdf"),
                    drive_file("file_4", "four.pdf"),
                ],
            },
        },
        fields={
            "file_1": {
                "DaIngest": True,
            },
            "file_2": {
                "DaIngest": False,
            },
            "file_3": {
                "DaIngest": True,
            },
            "file_4": {
                "DaIngest": False,
            },
        },
    )

    page = await SharePointDiscoveryProvider(graph_client).discover(
        source(),
        limit=10,
    )

    assert [
        item.external_file_id
        for item in page.items
    ] == [
        "file_2",
        "file_4",
    ]


@pytest.mark.asyncio
async def test_discovery_folder_traversal_still_discovers_child_files():
    graph_client = FakeGraphClient(
        pages={
            "/sites/site/drives/drive/root/children": {
                "value": [
                    drive_folder("folder_1", "Folder"),
                ],
            },
            "/sites/site/drives/drive/items/folder_1/children": {
                "value": [
                    drive_file("file_1", "child.pdf"),
                ],
            },
        },
        fields={
            "file_1": {
                "DaIngest": False,
            },
        },
    )

    page = await SharePointDiscoveryProvider(graph_client).discover(
        source(),
        limit=10,
    )

    assert [
        item.external_file_id
        for item in page.items
    ] == [
        "file_1",
    ]
    assert graph_client.page_calls == [
        "/sites/site/drives/drive/root/children",
        "/sites/site/drives/drive/items/folder_1/children",
    ]


@pytest.mark.asyncio
async def test_discovery_metadata_error_is_not_treated_as_not_ingested():
    graph_client = FakeGraphClient(
        pages={
            "/sites/site/drives/drive/root/children": {
                "value": [
                    drive_file("file_1", "one.pdf"),
                ],
            },
        },
        fields={},
        field_errors={
            "file_1": RuntimeError("Graph metadata failed"),
        },
    )

    with pytest.raises(RuntimeError, match="Graph metadata failed"):
        await SharePointDiscoveryProvider(graph_client).discover(
            source(),
            limit=10,
        )

    assert graph_client.field_calls == [
        (
            "file_1",
            {
                "$expand": "fields",
            },
        ),
    ]


@pytest.mark.asyncio
async def test_discovery_limit_counts_returned_files_not_skipped_files():
    graph_client = FakeGraphClient(
        pages={
            "/sites/site/drives/drive/root/children": {
                "value": [
                    drive_file("file_1", "one.pdf"),
                    drive_file("file_2", "two.pdf"),
                ],
                "@odata.nextLink": "next-page",
            },
            "next-page": {
                "value": [
                    drive_file("file_3", "three.pdf"),
                ],
            },
        },
        fields={
            "file_1": {
                "DaIngest": True,
            },
            "file_2": {
                "DaIngest": False,
            },
            "file_3": {
                "DaIngest": False,
            },
        },
    )

    page = await SharePointDiscoveryProvider(graph_client).discover(
        source(),
        limit=2,
    )

    assert [
        item.external_file_id
        for item in page.items
    ] == [
        "file_2",
        "file_3",
    ]
    assert page.has_more is False
    assert page.next_cursor is None
    assert graph_client.page_calls == [
        "/sites/site/drives/drive/root/children",
        "next-page",
    ]
    assert graph_client.field_calls == [
        (
            "file_1",
            {
                "$expand": "fields",
            },
        ),
        (
            "file_2",
            {
                "$expand": "fields",
            },
        ),
        (
            "file_3",
            {
                "$expand": "fields",
            },
        ),
    ]


@pytest.mark.asyncio
async def test_discovery_cursor_offset_advances_past_skipped_files():
    graph_client = FakeGraphClient(
        pages={
            "/sites/site/drives/drive/root/children": {
                "value": [
                    drive_file("file_1", "one.pdf"),
                    drive_file("file_2", "two.pdf"),
                    drive_file("file_3", "three.pdf"),
                ],
            },
        },
        fields={
            "file_1": {
                "DaIngest": True,
            },
            "file_2": {
                "DaIngest": False,
            },
            "file_3": {
                "DaIngest": False,
            },
        },
    )
    provider = SharePointDiscoveryProvider(graph_client)

    first_page = await provider.discover(
        source(),
        limit=1,
    )

    assert [
        item.external_file_id
        for item in first_page.items
    ] == [
        "file_2",
    ]
    assert first_page.has_more is True
    assert first_page.next_cursor == {
        "current_page_url": "/sites/site/drives/drive/root/children",
        "item_offset": 2,
        "pending_endpoints": [],
    }

    second_page = await provider.discover(
        source(),
        cursor=first_page.next_cursor,
        limit=1,
    )

    assert [
        item.external_file_id
        for item in second_page.items
    ] == [
        "file_3",
    ]
    assert second_page.has_more is False
    assert second_page.next_cursor is None


class FakeGraphClient:
    def __init__(self, *, pages, fields, field_errors=None):
        self._pages = pages
        self._fields = fields
        self._field_errors = field_errors or {}
        self.page_calls = []
        self.field_calls = []

    async def get(self, endpoint, *, params=None):
        if endpoint.endswith("/listItem"):
            item_id = endpoint.split("/items/", 1)[1].split("/", 1)[0]
            self.field_calls.append(
                (
                    item_id,
                    params,
                )
            )
            if item_id in self._field_errors:
                raise self._field_errors[item_id]
            return {
                "fields": self._fields.get(item_id, {}),
            }

        self.page_calls.append(endpoint)
        return self._pages[endpoint]


def source():
    return SourceReference(
        provider="sharepoint",
        identifier="source",
        metadata={
            "site_id": "site",
            "drive_id": "drive",
        },
    )


def drive_file(item_id, name):
    return {
        "id": item_id,
        "name": name,
        "file": {
            "mimeType": "application/pdf",
        },
        "size": 123,
        "webUrl": f"https://example.test/{name}",
        "parentReference": {
            "id": "parent",
            "path": "/drives/drive/root:",
        },
        "lastModifiedDateTime": "2024-01-01T00:00:00Z",
    }


def drive_folder(item_id, name):
    return {
        "id": item_id,
        "name": name,
        "folder": {},
        "parentReference": {
            "id": "parent",
            "path": "/drives/drive/root:",
        },
    }
