from __future__ import annotations

import httpx

from module.data_platform.common.microsoft_graph.authentication.token_provider import (
    TokenProvider,
)


class ClientSecretGraphTokenProvider(TokenProvider):
    def __init__(
        self,
        *,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        scope: str,
    ) -> None:
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._scope = scope

    async def get_token(self) -> str:
        url = (
            "https://login.microsoftonline.com/"
            f"{self._tenant_id}/oauth2/v2.0/token"
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                data={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "scope": self._scope,
                    "grant_type": "client_credentials",
                },
            )

            response.raise_for_status()

            return str(response.json()["access_token"])
