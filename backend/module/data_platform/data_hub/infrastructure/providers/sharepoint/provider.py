from __future__ import annotations

from module.data_platform.common.microsoft_graph.client import (
    MicrosoftGraphClient,
)
from module.data_platform.data_hub.domain.contracts.discovery_provider import (
    DiscoveryProvider,
)
from module.data_platform.data_hub.domain.contracts.file_downloader import (
    FileDownloader,
)
from module.data_platform.data_hub.domain.contracts.browse_provider import (
    BrowseProvider,
)

from .browser import SharePointBrowseProvider
from .discovery import SharePointDiscoveryProvider
from .downloader import SharePointFileDownloader


class SharePointProvider:
    """
    Composition root for SharePoint Data Hub capabilities.
    """

    def __init__(
        self,
        graph_client: MicrosoftGraphClient,
    ) -> None:
        self.discovery: DiscoveryProvider = (
            SharePointDiscoveryProvider(graph_client)
        )

        self.downloader: FileDownloader = (
            SharePointFileDownloader(graph_client)
        )

        self.browser: BrowseProvider = (
            SharePointBrowseProvider(graph_client)
        )
