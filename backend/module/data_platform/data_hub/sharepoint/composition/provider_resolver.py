from __future__ import annotations

import logging

from module.data_platform.common.microsoft_graph.client import (
    MicrosoftGraphClient,
)
from module.data_platform.common.microsoft_graph.authentication.token_provider import (
    TokenProvider,
)
from module.data_platform.data_hub.sharepoint.infrastructure.provider import (
    SharePointProvider,
)
from shared.config.settings import settings


logger = logging.getLogger(__name__)


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
        provider_code = provider.strip().lower()
        logger.info(
            "data_hub provider_resolve provider=%s",
            provider_code,
        )

        if provider_code == "sharepoint":
            graph_client = MicrosoftGraphClient(
                token_provider=self._token_provider,
                base_url=settings.GRAPH_BASE_URL,
            )

            return SharePointProvider(
                graph_client=graph_client,
            )

        logger.error(
            "data_hub provider_unsupported provider=%s",
            provider_code,
        )
        raise ValueError(
            f"Unsupported Data Hub provider: {provider}"
        )
