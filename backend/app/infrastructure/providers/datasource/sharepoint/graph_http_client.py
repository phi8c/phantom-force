import httpx

from app.infrastructure.providers.datasource.sharepoint.azure_ad_token_provider import (
    AzureAdTokenProvider,
)


class GraphHttpClient:

    def __init__(
        self,
        token_provider: AzureAdTokenProvider,
        base_url: str,
    ):
        self.token_provider = token_provider
        self.base_url = base_url

    async def get(
        self,
        endpoint: str,
    ):

        token = await (
            self.token_provider.get_token()
        )

        async with httpx.AsyncClient() as client:

            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers={
                    "Authorization":
                    f"Bearer {token}",
                },
            )

            print("=" * 100)
            print(
                "GRAPH URL =",
                f"{self.base_url}{endpoint}",
            )
            print(
                "STATUS =",
                response.status_code,
            )
            print(
                "BODY =",
                response.text,
            )
            print("=" * 100)

            response.raise_for_status()

            return response.json()
        
    async def download(
        self,
        endpoint: str,
    ) -> bytes:

        token = await (
            self.token_provider.get_token()
        )

        async with httpx.AsyncClient(
    follow_redirects=True,
) as client:

            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers={
                    "Authorization":
                    f"Bearer {token}",
                },
            )

            response.raise_for_status()

            return response.content