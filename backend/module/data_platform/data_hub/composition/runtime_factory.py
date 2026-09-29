from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from typing import Any

from module.data_platform.common.microsoft_graph.authentication.factory import (
    create_graph_token_provider,
)
from module.data_platform.common.microsoft_graph.client import (
    MicrosoftGraphClient,
)
from module.data_platform.data_hub.dropbox.composition import (
    create_dropbox_provider,
)
from module.data_platform.data_hub.dropbox.domain.configuration import (
    DropboxConfiguration,
)
from module.data_platform.data_hub.dropbox.infrastructure.client import (
    DropboxHttpClient,
)
from module.data_platform.data_hub.dropbox.infrastructure.downloader import (
    DropboxFileDownloader,
)
from module.data_platform.data_hub.sharepoint.infrastructure.downloader import (
    SharePointFileDownloader,
)
from module.data_platform.data_hub.sharepoint.infrastructure.provider import (
    SharePointProvider,
)
from module.data_platform.data_hub.shared.domain.entities.discovered_file import (
    DiscoveredFile,
)
from shared.config.settings import settings

from .downloader_registry import (
    DataHubDownloaderRegistry,
    DataHubDownloaderResource,
)
from .provider_registry import DataHubProviderRegistry


def create_data_hub_provider_resolver() -> DataHubProviderRegistry:
    return DataHubProviderRegistry(
        {
            "sharepoint": _create_sharepoint_provider,
            "dropbox": create_dropbox_provider,
        }
    )


def create_data_hub_downloader_registry() -> DataHubDownloaderRegistry:
    return DataHubDownloaderRegistry(
        {
            "sharepoint": _create_sharepoint_downloader,
            "dropbox": _create_dropbox_downloader,
        }
    )


async def open_data_hub_download_stream(
    *,
    registry: DataHubDownloaderRegistry,
    provider: str,
    configuration: Mapping[str, Any],
    file: DiscoveredFile,
) -> AsyncIterator[bytes]:
    resource = registry.create(provider, configuration)
    try:
        async for chunk in resource.downloader.download_stream(file):
            yield chunk
    finally:
        await resource.close()


def _create_sharepoint_client() -> MicrosoftGraphClient:
    return MicrosoftGraphClient(
        token_provider=create_graph_token_provider(),
        base_url=settings.GRAPH_BASE_URL,
    )


def _create_sharepoint_provider(
    configuration: Mapping[str, Any],
) -> SharePointProvider:
    return SharePointProvider(
        graph_client=_create_sharepoint_client(),
    )


def _create_sharepoint_downloader(
    configuration: Mapping[str, Any],
) -> DataHubDownloaderResource:
    client = _create_sharepoint_client()
    return DataHubDownloaderResource(
        downloader=SharePointFileDownloader(client),
        _close_callback=client.close,
    )


def _create_dropbox_downloader(
    configuration: Mapping[str, Any],
) -> DataHubDownloaderResource:
    client = DropboxHttpClient(
        DropboxConfiguration.from_mapping(configuration)
    )
    return DataHubDownloaderResource(
        downloader=DropboxFileDownloader(client),
        _close_callback=client.close,
    )
