import httpx

from app.shared.config.settings import (
    settings,
)


class AzureAdTokenProvider:

    async def get_token(
        self,
    ) -> str:

        async with httpx.AsyncClient() as client:

            response = await client.post(
                f"https://login.microsoftonline.com/"
                f"{settings.GRAPH_TENANT_ID}"
                f"/oauth2/v2.0/token",
                data={
                    "client_id":
                    settings.GRAPH_CLIENT_ID,

                    "client_secret":
                    settings.GRAPH_CLIENT_SECRET,

                    "scope":
                    settings.GRAPH_SCOPE,

                    "grant_type":
                    "client_credentials",
                },
            )

            response.raise_for_status()

            data = response.json()

            return data[
                "access_token"
            ]