from __future__ import annotations

import unittest
from unittest.mock import patch

from module.data_platform.data_hub.composition.downloader_registry import (
    UnsupportedDataHubDownloaderError,
)
from module.data_platform.data_hub.composition.provider_registry import (
    UnsupportedDataHubProviderError,
)
from module.data_platform.data_hub.composition.runtime_factory import (
    create_data_hub_downloader_registry,
    create_data_hub_provider_resolver,
)
from module.data_platform.data_hub.dropbox.infrastructure.downloader import (
    DropboxFileDownloader,
)
from module.data_platform.data_hub.sharepoint.infrastructure.downloader import (
    SharePointFileDownloader,
)


class FakeClient:
    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True


class DataHubProviderRuntimeTests(unittest.TestCase):
    def test_resolves_sharepoint_provider(self) -> None:
        provider = object()
        with patch(
            "module.data_platform.data_hub.composition.runtime_factory._create_sharepoint_provider",
            return_value=provider,
        ):
            resolver = create_data_hub_provider_resolver()
            self.assertIs(resolver.resolve("sharepoint", {}), provider)

    def test_resolves_dropbox_without_calling_sharepoint(self) -> None:
        provider = object()
        with (
            patch(
                "module.data_platform.data_hub.composition.runtime_factory._create_sharepoint_provider",
                side_effect=AssertionError("SharePoint must not be constructed"),
            ),
            patch(
                "module.data_platform.data_hub.composition.runtime_factory.create_dropbox_provider",
                return_value=provider,
            ),
        ):
            resolver = create_data_hub_provider_resolver()
            self.assertIs(
                resolver.resolve(
                    "dropbox",
                    {
                        "app_key": "key",
                        "app_secret": "secret",
                        "refresh_token": "token",
                    },
                ),
                provider,
            )

    def test_unknown_provider_fails_clearly(self) -> None:
        resolver = create_data_hub_provider_resolver()
        with self.assertRaisesRegex(
            UnsupportedDataHubProviderError,
            "Unsupported Data Hub provider",
        ):
            resolver.resolve("unknown", {})


class DataHubDownloaderRuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_sharepoint_uses_sharepoint_downloader_only(self) -> None:
        client = FakeClient()
        with (
            patch(
                "module.data_platform.data_hub.composition.runtime_factory._create_sharepoint_client",
                return_value=client,
            ),
            patch(
                "module.data_platform.data_hub.composition.runtime_factory.DropboxHttpClient",
                side_effect=AssertionError("Dropbox must not be constructed"),
            ),
        ):
            resource = create_data_hub_downloader_registry().create(
                "sharepoint",
                {},
            )

        self.assertIsInstance(resource.downloader, SharePointFileDownloader)
        await resource.close()
        self.assertTrue(client.closed)

    async def test_dropbox_uses_dropbox_downloader_only(self) -> None:
        client = FakeClient()
        configuration = {
            "app_key": "key",
            "app_secret": "secret",
            "refresh_token": "token",
        }
        with (
            patch(
                "module.data_platform.data_hub.composition.runtime_factory._create_sharepoint_client",
                side_effect=AssertionError("SharePoint must not be constructed"),
            ),
            patch(
                "module.data_platform.data_hub.composition.runtime_factory.DropboxHttpClient",
                return_value=client,
            ),
        ):
            resource = create_data_hub_downloader_registry().create(
                "dropbox",
                configuration,
            )

        self.assertIsInstance(resource.downloader, DropboxFileDownloader)
        await resource.close()
        self.assertTrue(client.closed)

    async def test_dropbox_configuration_is_isolated_per_resolution(self) -> None:
        clients: list[FakeClient] = []
        configurations = []

        def create_client(configuration):
            configurations.append(configuration)
            client = FakeClient()
            clients.append(client)
            return client

        with patch(
            "module.data_platform.data_hub.composition.runtime_factory.DropboxHttpClient",
            side_effect=create_client,
        ):
            registry = create_data_hub_downloader_registry()
            first = registry.create(
                "dropbox",
                {
                    "app_key": "key-a",
                    "app_secret": "secret-a",
                    "refresh_token": "token-a",
                },
            )
            second = registry.create(
                "dropbox",
                {
                    "app_key": "key-b",
                    "app_secret": "secret-b",
                    "refresh_token": "token-b",
                },
            )

        self.assertEqual(configurations[0].app_key, "key-a")
        self.assertEqual(configurations[1].app_key, "key-b")
        self.assertIsNot(clients[0], clients[1])
        await first.close()
        await second.close()

    def test_unknown_downloader_fails_clearly(self) -> None:
        with self.assertRaisesRegex(
            UnsupportedDataHubDownloaderError,
            "Unsupported Data Hub download provider",
        ):
            create_data_hub_downloader_registry().create("unknown", {})


if __name__ == "__main__":
    unittest.main()
