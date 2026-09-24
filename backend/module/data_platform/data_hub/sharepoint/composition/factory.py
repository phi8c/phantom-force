from __future__ import annotations

from module.data_platform.common.microsoft_graph.authentication.token_provider import (
    TokenProvider,
)

from module.data_platform.data_hub.api.data_hub import (
    DataHub,
)

from module.data_platform.data_hub.sharepoint.application.services.data_hub_service import (
    DataHubService,
)

from module.data_platform.data_hub.sharepoint.application.use_cases.discovery_files import (
    DiscoverFilesUseCase,
)

from module.data_platform.data_hub.sharepoint.application.use_cases.browse_sharepoint import (
    BrowseSharePointUseCase,
)
from module.data_platform.data_hub.sharepoint.application.use_cases.download_file import (
    DownloadFileUseCase,
)

from module.data_platform.data_hub.sharepoint.composition.provider_resolver import (
    DataHubProviderResolver,
)


def create_data_hub(
    token_provider: TokenProvider,
    provider: str = "sharepoint",
    configuration: dict | None = None,
) -> DataHub:

    resolver = DataHubProviderResolver(
        token_provider=token_provider,
    )

    data_hub_provider = resolver.resolve(
        provider=provider,
        configuration=configuration,
    )

    discover_files = DiscoverFilesUseCase(
        discovery_provider=(
            data_hub_provider.discovery
        ),
    )

    download_file = DownloadFileUseCase(
        file_downloader=(
            data_hub_provider.downloader
        ),
    )

    service = DataHubService(
        discover_files=discover_files,
        download_file=download_file,
        browse_sharepoint=BrowseSharePointUseCase(
            browse_provider=data_hub_provider.browser,
        ),
    )

    return DataHub(
        service=service,
    )
