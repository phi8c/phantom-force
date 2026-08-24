from __future__ import annotations

from module.data_platform.common.microsoft_graph.client import (
    MicrosoftGraphClient,
)
from module.data_platform.common.microsoft_graph.authentication.token_provider import (
    TokenProvider,
)
from module.data_platform.data_hub.api import DataHub
from module.data_platform.data_hub.application.services.data_hub_service import (
    DataHubService,
)
from module.data_platform.data_hub.application.use_cases.discovery_files import (
    DiscoverFilesUseCase,
)
from module.data_platform.data_hub.application.use_cases.download_file import (
    DownloadFileUseCase,
)
from module.data_platform.data_hub.infrastructure.providers.sharepoint.provider import (
    SharePointProvider,
)


def create_data_hub(
    token_provider: TokenProvider,
) -> DataHub:
    graph_client = MicrosoftGraphClient(
        token_provider=token_provider,
    )

    sharepoint_provider = SharePointProvider(
        graph_client=graph_client,
    )

    discover_files = DiscoverFilesUseCase(
        discovery_provider=sharepoint_provider.discovery,
    )

    download_file = DownloadFileUseCase(
        file_downloader=sharepoint_provider.downloader,
    )

    service = DataHubService(
        discover_files=discover_files,
        download_file=download_file,
    )

    return DataHub(
        service=service,
    )