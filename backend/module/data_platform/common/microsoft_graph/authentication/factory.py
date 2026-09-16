from __future__ import annotations

from module.data_platform.common.microsoft_graph.authentication.client_secret_token_provider import (
    ClientSecretGraphTokenProvider,
)
from module.data_platform.common.microsoft_graph.authentication.token_provider import (
    TokenProvider,
)
from shared.config.settings import settings


def create_graph_token_provider() -> TokenProvider:
    required = {
        "GRAPH_TENANT_ID": settings.GRAPH_TENANT_ID,
        "GRAPH_CLIENT_ID": settings.GRAPH_CLIENT_ID,
        "GRAPH_CLIENT_SECRET": settings.GRAPH_CLIENT_SECRET,
        "GRAPH_SCOPE": settings.GRAPH_SCOPE,
    }

    missing = [
        name
        for name, value in required.items()
        if not value
    ]

    if missing:
        raise RuntimeError(
            "Missing Microsoft Graph settings: "
            + ", ".join(missing)
        )

    return ClientSecretGraphTokenProvider(
        tenant_id=str(settings.GRAPH_TENANT_ID),
        client_id=str(settings.GRAPH_CLIENT_ID),
        client_secret=str(settings.GRAPH_CLIENT_SECRET),
        scope=str(settings.GRAPH_SCOPE),
    )
