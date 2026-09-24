from __future__ import annotations

from collections.abc import Mapping

from module.data_platform.common.microsoft_graph.authentication.factory import (
    create_graph_token_provider,
)
from module.data_platform.common.microsoft_graph.client import MicrosoftGraphClient
from module.data_platform.data_hub.dropbox.application.adapters.browser import (
    DropboxBrowserAdapter,
)
from module.data_platform.data_hub.dropbox.domain.configuration import DropboxConfiguration
from module.data_platform.data_hub.dropbox.infrastructure.browser import DropboxBrowseProvider
from module.data_platform.data_hub.dropbox.infrastructure.client import DropboxHttpClient
from module.data_platform.data_hub.sharepoint.application.adapters.browser import (
    SharePointBrowserAdapter,
)
from module.data_platform.data_hub.sharepoint.infrastructure.browser import (
    SharePointBrowseProvider,
)
from shared.config.settings import settings

from .browser_registry import DataHubBrowserProviderRegistry


def create_browser_provider_registry() -> DataHubBrowserProviderRegistry:
    return DataHubBrowserProviderRegistry(
        {"sharepoint": _create_sharepoint_browser, "dropbox": _create_dropbox_browser}
    )


def _create_sharepoint_browser(
    configuration: Mapping[str, object],
) -> SharePointBrowserAdapter:
    graph_client = MicrosoftGraphClient(
        token_provider=create_graph_token_provider(),
        base_url=settings.GRAPH_BASE_URL,
    )
    return SharePointBrowserAdapter(
        SharePointBrowseProvider(graph_client),
        graph_client,
    )


def _create_dropbox_browser(
    configuration: Mapping[str, object],
) -> DropboxBrowserAdapter:
    resolved = DropboxConfiguration.from_mapping(configuration)
    client = DropboxHttpClient(resolved)
    return DropboxBrowserAdapter(
        DropboxBrowseProvider(client, resolved),
        client,
    )
