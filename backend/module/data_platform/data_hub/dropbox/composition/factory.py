from __future__ import annotations

from typing import Any, Mapping

from ..domain.configuration import DropboxConfiguration
from ..domain.contracts.client import DropboxClient
from ..infrastructure.browser import DropboxBrowseProvider
from ..infrastructure.client import DropboxSdkClient
from ..infrastructure.discovery import DropboxDiscoveryProvider
from ..infrastructure.downloader import DropboxFileDownloader
from ..provider import DropboxProvider


def create_dropbox_provider(
    configuration: DropboxConfiguration | Mapping[str, Any],
    *,
    client: DropboxClient | None = None,
) -> DropboxProvider:
    resolved_configuration = (
        configuration
        if isinstance(configuration, DropboxConfiguration)
        else DropboxConfiguration.from_mapping(configuration)
    )
    resolved_client = client or DropboxSdkClient(resolved_configuration)
    return DropboxProvider(
        browser=DropboxBrowseProvider(resolved_client, resolved_configuration),
        discovery=DropboxDiscoveryProvider(resolved_client, resolved_configuration),
        downloader=DropboxFileDownloader(resolved_client),
    )
