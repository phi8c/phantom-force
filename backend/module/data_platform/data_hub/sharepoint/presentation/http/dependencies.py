from __future__ import annotations

from module.data_platform.common.microsoft_graph.client import (
    MicrosoftGraphClient,
)
from module.data_platform.common.microsoft_graph.authentication.token_provider import (
    TokenProvider,
)
from module.data_platform.data_hub.sharepoint.application.services.data_hub_service import (
    DataHubService,
)
from module.data_platform.data_hub.sharepoint.application.use_cases.browse_sharepoint import (
    BrowseSharePointUseCase,
)
from module.data_platform.data_hub.sharepoint.application.use_cases.discovery_files import (
    DiscoverFilesUseCase,
)
from module.data_platform.data_hub.sharepoint.application.use_cases.download_file import (
    DownloadFileUseCase,
)
from module.data_platform.data_hub.sharepoint.infrastructure.provider import (
    SharePointProvider,
)
from shared.config.settings import settings


def build_data_hub_service(
    token_provider: TokenProvider,
) -> DataHubService:
    graph_client = MicrosoftGraphClient(
        token_provider=token_provider,
        base_url=settings.GRAPH_BASE_URL,
    )

    sharepoint_provider = SharePointProvider(
        graph_client=graph_client,
    )

    return DataHubService(
        discover_files=DiscoverFilesUseCase(
            discovery_provider=sharepoint_provider.discovery,
        ),
        download_file=DownloadFileUseCase(
            file_downloader=sharepoint_provider.downloader,
        ),
        browse_sharepoint=BrowseSharePointUseCase(
            browse_provider=sharepoint_provider.browser,
        ),
    )
