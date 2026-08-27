from __future__ import annotations

from module.data_platform.common.microsoft_graph.client import (
    MicrosoftGraphClient,
)
from module.data_platform.common.microsoft_graph.authentication.token_provider import (
    TokenProvider,
)
from module.data_platform.data_hub.infrastructure.providers.sharepoint.provider import (
    SharePointProvider,
)


class DataHubProviderResolver:

    def __init__(
        self,
        token_provider: TokenProvider,
    ) -> None:
        self._token_provider = token_provider

    def resolve(
        self,
        provider: str,
        configuration: dict | None = None,
    ):
        provider_name = provider.strip().lower()

        if provider_name == "sharepoint":
            graph_client = MicrosoftGraphClient(
                token_provider=self._token_provider,
            )

            return SharePointProvider(
                graph_client=graph_client,
            )

        raise ValueError(
            f"Unsupported Data Hub provider: {provider}"
        )