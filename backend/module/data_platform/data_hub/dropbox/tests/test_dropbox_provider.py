from __future__ import annotations

import unittest
from datetime import datetime, timezone

from module.data_platform.data_hub.dropbox.composition.factory import (
    create_dropbox_provider,
)
from module.data_platform.data_hub.dropbox.domain.configuration import (
    DropboxConfiguration,
)
from module.data_platform.data_hub.dropbox.domain.entities.client_models import (
    DropboxEntry,
    DropboxListPage,
)
from module.data_platform.data_hub.shared.domain.value_objects.source_reference import (
    SourceReference,
)


def file_entry(name: str, path: str, *, size: int = 10) -> DropboxEntry:
    return DropboxEntry(
        kind="file",
        id=f"id:{path}",
        name=name,
        path_lower=path.lower(),
        path_display=path,
        size=size,
        server_modified=datetime(2026, 1, 2, tzinfo=timezone.utc),
        rev=f"rev-{name}",
        content_hash=f"hash-{name}",
    )


def folder_entry(name: str, path: str) -> DropboxEntry:
    return DropboxEntry(
        kind="folder",
        id=f"id:{path}",
        name=name,
        path_lower=path.lower(),
        path_display=path,
    )


class FakeDropboxClient:
    def __init__(self) -> None:
        self.list_pages: dict[tuple[str, bool], DropboxListPage] = {}
        self.continuation_pages: dict[str, DropboxListPage] = {}
        self.downloads: dict[str, bytes] = {}
        self.list_calls: list[tuple[str, bool]] = []
        self.continue_calls: list[str] = []
        self.download_calls: list[str] = []

    async def list_folder(self, path: str, *, recursive: bool) -> DropboxListPage:
        self.list_calls.append((path, recursive))
        return self.list_pages[(path, recursive)]

    async def list_folder_continue(self, cursor: str) -> DropboxListPage:
        self.continue_calls.append(cursor)
        return self.continuation_pages[cursor]

    async def download(self, identity: str) -> bytes:
        self.download_calls.append(identity)
        return self.downloads[identity]


class DropboxConfigurationTests(unittest.TestCase):
    def test_requires_all_refresh_token_credentials(self) -> None:
        for missing in ("app_key", "app_secret", "refresh_token"):
            value = {
                "app_key": "key",
                "app_secret": "secret",
                "refresh_token": "refresh",
            }
            del value[missing]
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                DropboxConfiguration.from_mapping(value)

    def test_normalizes_root_and_rejects_paths_outside_it(self) -> None:
        configuration = DropboxConfiguration.from_mapping(
            {
                "app_key": "key",
                "app_secret": "secret",
                "refresh_token": "refresh",
                "root_path": "\\RT_Test\\Docs\\",
            }
        )
        self.assertEqual(configuration.root_path, "/RT_Test/Docs")
        self.assertEqual(configuration.resolve_path("/rt_test/docs/A"), "/rt_test/docs/A")
        with self.assertRaises(ValueError):
            configuration.resolve_path("/Elsewhere")


class DropboxProviderTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.client = FakeDropboxClient()
        self.provider = create_dropbox_provider(
            {
                "app_key": "key",
                "app_secret": "secret",
                "refresh_token": "refresh",
                "root_path": "/RT_Test",
            },
            client=self.client,
        )

    async def test_browser_lists_only_direct_children_and_drains_api_pages(self) -> None:
        self.client.list_pages[("/RT_Test", False)] = DropboxListPage(
            entries=[folder_entry("Docs", "/RT_Test/Docs")],
            cursor="browse-next",
            has_more=True,
        )
        self.client.continuation_pages["browse-next"] = DropboxListPage(
            entries=[file_entry("readme.txt", "/RT_Test/readme.txt")]
        )
        self.client.list_pages[("/RT_Test/Docs", False)] = DropboxListPage(
            entries=[file_entry("a.pdf", "/RT_Test/Docs/a.pdf")]
        )

        root = await self.provider.browser.list_root_children()
        folder = await self.provider.browser.list_folder_children("/RT_Test/Docs")

        self.assertEqual([node.name for node in root], ["Docs", "readme.txt"])
        self.assertEqual([node.name for node in folder], ["a.pdf"])
        self.assertEqual(
            self.client.list_calls,
            [("/RT_Test", False), ("/RT_Test/Docs", False)],
        )

    async def test_discovery_is_recursive_and_normalizes_shared_files(self) -> None:
        self.client.list_pages[("/RT_Test", True)] = DropboxListPage(
            entries=[
                folder_entry("Docs", "/RT_Test/Docs"),
                file_entry("report.PDF", "/RT_Test/Docs/report.PDF", size=42),
            ]
        )
        source = SourceReference(provider="dropbox", identifier="/RT_Test")

        page = await self.provider.discovery.discover(source)

        self.assertFalse(page.has_more)
        self.assertEqual(len(page.items), 1)
        self.assertEqual(page.items[0].file_extension, "pdf")
        self.assertEqual(page.items[0].file_size_bytes, 42)
        self.assertIs(page.items[0].source, source)
        self.assertEqual(self.client.list_calls, [("/RT_Test", True)])

    async def test_discovery_supports_one_selected_root(self) -> None:
        self.client.list_pages[("/RT_Test/A", True)] = DropboxListPage(
            entries=[file_entry("a.txt", "/RT_Test/A/a.txt")]
        )
        source = SourceReference(
            provider="dropbox",
            identifier="data-hub-id",
            metadata={"roots": [{"locator": {"path": "/RT_Test/A"}}]},
        )

        page = await self.provider.discovery.discover(source)

        self.assertEqual([item.file_name for item in page.items], ["a.txt"])
        self.assertEqual(self.client.list_calls, [("/RT_Test/A", True)])

    async def test_discovery_supports_multiple_selected_roots(self) -> None:
        self.client.list_pages[("/RT_Test/A", True)] = DropboxListPage(
            entries=[file_entry("a.txt", "/RT_Test/A/a.txt")]
        )
        self.client.list_pages[("/RT_Test/B", True)] = DropboxListPage(
            entries=[file_entry("b.txt", "/RT_Test/B/b.txt")]
        )
        source = self._multi_root_source()

        page = await self.provider.discovery.discover(source)

        self.assertEqual(
            [item.file_name for item in page.items],
            ["a.txt", "b.txt"],
        )
        self.assertFalse(page.has_more)

    async def test_pagination_resumes_when_moving_to_next_root(self) -> None:
        self.client.list_pages[("/RT_Test/A", True)] = DropboxListPage(
            entries=[file_entry("a.txt", "/RT_Test/A/a.txt")]
        )
        self.client.list_pages[("/RT_Test/B", True)] = DropboxListPage(
            entries=[file_entry("b.txt", "/RT_Test/B/b.txt")]
        )
        source = self._multi_root_source()

        first = await self.provider.discovery.discover(source, limit=1)
        second = await self.provider.discovery.discover(
            source,
            cursor=first.next_cursor,
            limit=1,
        )

        self.assertEqual([item.file_name for item in first.items], ["a.txt"])
        self.assertEqual([item.file_name for item in second.items], ["b.txt"])
        self.assertTrue(first.has_more)
        self.assertFalse(second.has_more)
        self.assertEqual(
            self.client.list_calls,
            [("/RT_Test/A", True), ("/RT_Test/B", True)],
        )

    async def test_multi_root_batch_limit_applies_across_roots(self) -> None:
        self.client.list_pages[("/RT_Test/A", True)] = DropboxListPage(
            entries=[
                file_entry("a1.txt", "/RT_Test/A/a1.txt"),
                file_entry("a2.txt", "/RT_Test/A/a2.txt"),
            ]
        )
        self.client.list_pages[("/RT_Test/B", True)] = DropboxListPage(
            entries=[file_entry("b.txt", "/RT_Test/B/b.txt")]
        )
        source = self._multi_root_source()

        first = await self.provider.discovery.discover(source, limit=2)
        second = await self.provider.discovery.discover(
            source, cursor=first.next_cursor, limit=2
        )

        self.assertEqual(len(first.items), 2)
        self.assertEqual([item.file_name for item in second.items], ["b.txt"])

    async def test_discovery_rejects_invalid_dropbox_locator(self) -> None:
        source = SourceReference(
            provider="dropbox",
            identifier="data-hub-id",
            metadata={"roots": [{"locator": {}}]},
        )
        with self.assertRaisesRegex(ValueError, "path"):
            await self.provider.discovery.discover(source)

    async def test_discovery_rejects_sharepoint_locator(self) -> None:
        source = SourceReference(
            provider="dropbox",
            identifier="data-hub-id",
            metadata={
                "roots": [
                    {"locator": {"site_id": "site", "drive_id": "drive"}}
                ]
            },
        )
        with self.assertRaisesRegex(ValueError, "SharePoint locator"):
            await self.provider.discovery.discover(source)

    async def test_pagination_resumes_without_restart_duplicate_or_loss(self) -> None:
        self.client.list_pages[("/RT_Test", True)] = DropboxListPage(
            entries=[
                folder_entry("Nested", "/RT_Test/Nested"),
                file_entry("a.txt", "/RT_Test/a.txt"),
                file_entry("b.txt", "/RT_Test/b.txt"),
                file_entry("c.txt", "/RT_Test/Nested/c.txt"),
            ],
            cursor="sdk-next",
            has_more=True,
        )
        self.client.continuation_pages["sdk-next"] = DropboxListPage(
            entries=[file_entry("d.txt", "/RT_Test/Nested/d.txt")]
        )
        source = SourceReference(provider="dropbox", identifier="/RT_Test")

        first = await self.provider.discovery.discover(source, limit=2)
        second = await self.provider.discovery.discover(
            source, cursor=first.next_cursor, limit=2
        )

        names = [file.file_name for file in first.items + second.items]
        self.assertEqual(names, ["a.txt", "b.txt", "c.txt", "d.txt"])
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(first.has_more)
        self.assertFalse(second.has_more)
        self.assertEqual(self.client.list_calls, [("/RT_Test", True)])
        self.assertEqual(self.client.continue_calls, ["sdk-next"])

    async def test_downloader_uses_discovery_metadata_and_streams_chunks(self) -> None:
        self.client.list_pages[("/RT_Test", True)] = DropboxListPage(
            entries=[file_entry("a.txt", "/RT_Test/a.txt")]
        )
        source = SourceReference(provider="dropbox", identifier="/RT_Test")
        discovered = (await self.provider.discovery.discover(source)).items[0]
        identity = str(discovered.provider_metadata["id"])
        self.client.downloads[identity] = b"downloaded"

        content = await self.provider.downloader.download(discovered)
        streamed = b"".join(
            [chunk async for chunk in self.provider.downloader.download_stream(discovered)]
        )

        self.assertEqual(content, b"downloaded")
        self.assertEqual(streamed, content)
        self.assertEqual(self.client.download_calls, [identity, identity])

    async def test_discovery_rejects_non_dropbox_source(self) -> None:
        source = SourceReference(provider="sharepoint", identifier="/RT_Test")
        with self.assertRaises(ValueError):
            await self.provider.discovery.discover(source)

    @staticmethod
    def _multi_root_source() -> SourceReference:
        return SourceReference(
            provider="dropbox",
            identifier="data-hub-id",
            metadata={
                "roots": [
                    {"locator": {"path": "/RT_Test/A"}},
                    {"locator": {"path": "/RT_Test/B"}},
                ]
            },
        )


if __name__ == "__main__":
    unittest.main()
