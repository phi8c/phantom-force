from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from module.data_platform.data_hub.composition.browser_registry import (
    DataHubBrowserProviderRegistry,
    UnsupportedBrowserProviderError,
)
from module.data_platform.data_hub.shared.application.browser_service import (
    DataHubBrowserService,
)
from module.data_platform.data_hub.shared.domain.entities.browse_node import (
    DataHubBrowseNode,
)
from module.knowledge_space.application.services.data_hub_configuration_resolver import (
    DataHubConfigurationDisabledError,
    DataHubConfigurationNotFoundError,
    KnowledgeSpaceDataHubConfigurationResolver,
    ResolvedDataHubConfiguration,
)


class FakeBrowser:
    def __init__(self, provider: str, *, error: Exception | None = None) -> None:
        self.provider = provider
        self.error = error
        self.root_calls = 0
        self.child_locators = []
        self.close_calls = 0

    async def browse_root(self):
        self.root_calls += 1
        if self.error:
            raise self.error
        return [
            DataHubBrowseNode(
                id="node",
                name="Node",
                type="folder",
                has_children=True,
                provider=self.provider,
                locator={"path": "/safe"},
            )
        ]

    async def browse_children(self, locator):
        self.child_locators.append(locator)
        if self.error:
            raise self.error
        return []

    async def close(self):
        self.close_calls += 1


class FakeConfigurationResolver:
    def __init__(self, provider: str, configuration: dict | None = None) -> None:
        self.resolved = ResolvedDataHubConfiguration(
            data_hub_id=uuid4(),
            provider=provider,
            configuration=configuration or {},
        )

    async def resolve(self, knowledge_space_id):
        return self.resolved


class BrowserIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_dropbox_route_does_not_create_sharepoint(self) -> None:
        dropbox = FakeBrowser("dropbox")
        sharepoint_factory = unittest.mock.Mock()
        registry = DataHubBrowserProviderRegistry(
            {"dropbox": lambda config: dropbox, "sharepoint": sharepoint_factory}
        )
        service = DataHubBrowserService(
            FakeConfigurationResolver(
                "dropbox",
                {"app_secret": "secret", "refresh_token": "token"},
            ),
            registry,
        )

        result = await service.browse_root(uuid4())

        self.assertEqual(result.provider, "dropbox")
        self.assertEqual(result.nodes[0].locator, {"path": "/safe"})
        self.assertNotIn("secret", repr(result.nodes))
        self.assertNotIn("token", repr(result.nodes))
        sharepoint_factory.assert_not_called()
        self.assertEqual(dropbox.close_calls, 1)

    async def test_sharepoint_route_does_not_create_dropbox(self) -> None:
        sharepoint = FakeBrowser("sharepoint")
        dropbox_factory = unittest.mock.Mock()
        registry = DataHubBrowserProviderRegistry(
            {"sharepoint": lambda config: sharepoint, "dropbox": dropbox_factory}
        )
        service = DataHubBrowserService(
            FakeConfigurationResolver("sharepoint"), registry
        )

        await service.browse_children(uuid4(), {"kind": "site", "site_id": "s"})

        self.assertEqual(
            sharepoint.child_locators,
            [{"kind": "site", "site_id": "s"}],
        )
        dropbox_factory.assert_not_called()

    async def test_provider_failure_does_not_fallback(self) -> None:
        dropbox = FakeBrowser("dropbox", error=RuntimeError("dropbox failed"))
        sharepoint_factory = unittest.mock.Mock()
        service = DataHubBrowserService(
            FakeConfigurationResolver("dropbox"),
            DataHubBrowserProviderRegistry(
                {"dropbox": lambda config: dropbox, "sharepoint": sharepoint_factory}
            ),
        )

        with self.assertRaisesRegex(RuntimeError, "dropbox failed"):
            await service.browse_root(uuid4())

        sharepoint_factory.assert_not_called()
        self.assertEqual(dropbox.close_calls, 1)

    async def test_unknown_provider_fails_clearly(self) -> None:
        service = DataHubBrowserService(
            FakeConfigurationResolver("unknown"),
            DataHubBrowserProviderRegistry({"dropbox": lambda config: FakeBrowser("dropbox")}),
        )
        with self.assertRaises(UnsupportedBrowserProviderError):
            await service.browse_root(uuid4())


class ConfigurationResolverTests(unittest.IsolatedAsyncioTestCase):
    async def test_missing_mapping_fails(self) -> None:
        resolver = KnowledgeSpaceDataHubConfigurationResolver(
            SimpleNamespace(get_by_knowledge_space_id=AsyncMock(return_value=None)),
            SimpleNamespace(get_by_id=AsyncMock()),
        )

        with self.assertRaises(DataHubConfigurationNotFoundError):
            await resolver.resolve(uuid4())

    async def test_disabled_mapping_fails(self) -> None:
        mapping = SimpleNamespace(
            id=uuid4(),
            enabled=False,
            data_hub_provider_id=uuid4(),
            configuration={},
        )
        mapping_repository = SimpleNamespace(
            get_by_knowledge_space_id=AsyncMock(return_value=mapping)
        )
        provider_repository = SimpleNamespace(get_by_id=AsyncMock())
        resolver = KnowledgeSpaceDataHubConfigurationResolver(
            mapping_repository, provider_repository
        )

        with self.assertRaises(DataHubConfigurationDisabledError):
            await resolver.resolve(uuid4())

        provider_repository.get_by_id.assert_not_awaited()

    async def test_disabled_provider_fails(self) -> None:
        provider_id = uuid4()
        mapping = SimpleNamespace(
            id=uuid4(),
            enabled=True,
            data_hub_provider_id=provider_id,
            configuration={},
        )
        provider = SimpleNamespace(
            enabled=False, code="dropbox", provider="dropbox"
        )
        resolver = KnowledgeSpaceDataHubConfigurationResolver(
            SimpleNamespace(get_by_knowledge_space_id=AsyncMock(return_value=mapping)),
            SimpleNamespace(get_by_id=AsyncMock(return_value=provider)),
        )

        with self.assertRaises(DataHubConfigurationDisabledError):
            await resolver.resolve(uuid4())

    async def test_missing_provider_fails(self) -> None:
        mapping = SimpleNamespace(
            id=uuid4(),
            enabled=True,
            data_hub_provider_id=uuid4(),
            configuration={},
        )
        resolver = KnowledgeSpaceDataHubConfigurationResolver(
            SimpleNamespace(get_by_knowledge_space_id=AsyncMock(return_value=mapping)),
            SimpleNamespace(get_by_id=AsyncMock(return_value=None)),
        )

        with self.assertRaises(DataHubConfigurationNotFoundError):
            await resolver.resolve(uuid4())


if __name__ == "__main__":
    unittest.main()
