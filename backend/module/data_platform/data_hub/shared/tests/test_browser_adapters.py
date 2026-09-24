from __future__ import annotations

import unittest

from module.data_platform.data_hub.dropbox.application.adapters.browser import (
    DropboxBrowserAdapter,
)
from module.data_platform.data_hub.dropbox.domain.entities.browse_node import (
    DropboxBrowseNode,
)
from module.data_platform.data_hub.sharepoint.application.adapters.browser import (
    SharePointBrowserAdapter,
)
from module.data_platform.data_hub.sharepoint.domain.entities.browse_node import (
    BrowseNode,
)


class FakeSharePointBrowser:
    def __init__(self) -> None:
        self.calls = []

    async def list_sites(self):
        self.calls.append(("sites",))
        return [BrowseNode(id="site", name="Site", type="site", has_children=True)]

    async def list_drives(self, *, site_id):
        self.calls.append(("drives", site_id))
        return [BrowseNode(id="drive", name="Drive", type="drive", site_id=site_id)]

    async def list_drive_children(self, *, site_id, drive_id):
        self.calls.append(("drive_children", site_id, drive_id))
        return [BrowseNode(id="folder", name="Folder", type="folder", site_id=site_id, drive_id=drive_id)]

    async def list_folder_children(self, *, site_id, drive_id, folder_id):
        self.calls.append(("folder_children", site_id, drive_id, folder_id))
        return [BrowseNode(id="file", name="File", type="file", site_id=site_id, drive_id=drive_id)]


class FakeDropboxBrowser:
    def __init__(self) -> None:
        self.paths = []

    async def list_root_children(self):
        return []

    async def list_folder_children(self, path):
        self.paths.append(path)
        return [DropboxBrowseNode("id", "File", "file", "/folder/file", "/Folder/File", path, False)]


class BrowserAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_sharepoint_hierarchy_uses_opaque_locators(self) -> None:
        provider = FakeSharePointBrowser()
        browser = SharePointBrowserAdapter(provider)

        sites = await browser.browse_root()
        drives = await browser.browse_children(sites[0].locator)
        folders = await browser.browse_children(drives[0].locator)
        files = await browser.browse_children(folders[0].locator)

        self.assertEqual(files[0].locator["item_id"], "file")
        self.assertEqual(
            provider.calls,
            [
                ("sites",),
                ("drives", "site"),
                ("drive_children", "site", "drive"),
                ("folder_children", "site", "drive", "folder"),
            ],
        )

    async def test_dropbox_children_uses_path_locator(self) -> None:
        provider = FakeDropboxBrowser()
        browser = DropboxBrowserAdapter(provider)

        nodes = await browser.browse_children({"path": "/folder"})

        self.assertEqual(provider.paths, ["/folder"])
        self.assertEqual(nodes[0].locator, {"path": "/folder/file"})

    async def test_adapters_reject_other_provider_locator(self) -> None:
        with self.assertRaisesRegex(ValueError, "Dropbox locator"):
            await SharePointBrowserAdapter(FakeSharePointBrowser()).browse_children(
                {"path": "/folder"}
            )
        with self.assertRaisesRegex(ValueError, "SharePoint locator"):
            await DropboxBrowserAdapter(FakeDropboxBrowser()).browse_children(
                {"site_id": "site"}
            )


if __name__ == "__main__":
    unittest.main()
