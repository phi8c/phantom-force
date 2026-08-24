import httpx

from app.infrastructure.providers.datasource.sharepoint.auth_provider import (
    AuthProvider,
)


class GraphClient:

    GRAPH_BASE_URL = (
        "https://graph.microsoft.com/v1.0"
    )

    async def get_access_token(
        self,
    ) -> str:

        credential = (
            AuthProvider.get_credential()
        )

        token = (
            credential.get_token(
                "https://graph.microsoft.com/.default"
            )
        )

        return token.token

    async def get(
        self,
        endpoint: str,
    ):

        token = await (
            self.get_access_token()
        )

        async with httpx.AsyncClient() as client:

            response = await client.get(
                f"{self.GRAPH_BASE_URL}{endpoint}",
                headers={
                    "Authorization":
                    f"Bearer {token}",
                },
            )

            response.raise_for_status()

            return response.json()