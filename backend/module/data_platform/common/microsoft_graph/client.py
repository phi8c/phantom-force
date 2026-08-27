from __future__ import annotations

from typing import Any

import httpx

from .authentication.token_provider import TokenProvider
from .exceptions.client_exception import MicrosoftGraphClientError
from collections.abc import AsyncIterator


class MicrosoftGraphClient:

    def __init__(
        self,
        token_provider: TokenProvider,
        base_url: str = "https://graph.microsoft.com/v1.0",
        timeout: float = 60.0,
    ) -> None:
        self._token_provider = token_provider
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
        )

    async def _headers(self) -> dict[str, str]:
        token = await self._token_provider.get_token()

        return {
            "Authorization": f"Bearer {token}",
        }

    def _url(self, endpoint: str) -> str:
        if endpoint.startswith(("http://", "https://")):
            return endpoint

        return f"{self._base_url}/{endpoint.lstrip('/')}"
    async def get(
        self,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            response = await self._client.get(
                self._url(endpoint),
                headers=await self._headers(),
                params=params,
            )

            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as exc:
            raise MicrosoftGraphClientError(
                f"Microsoft Graph GET failed: {endpoint}"
            ) from exc

    async def post(
        self,
        endpoint: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            response = await self._client.post(
                self._url(endpoint),
                headers=await self._headers(),
                json=json,
                params=params,
            )

            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as exc:
            raise MicrosoftGraphClientError(
                f"Microsoft Graph POST failed: {endpoint}"
            ) from exc

    async def put(
        self,
        endpoint: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            response = await self._client.put(
                self._url(endpoint),
                headers=await self._headers(),
                json=json,
            )

            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as exc:
            raise MicrosoftGraphClientError(
                f"Microsoft Graph PUT failed: {endpoint}"
            ) from exc

    async def delete(
        self,
        endpoint: str,
    ) -> None:
        try:
            response = await self._client.delete(
                self._url(endpoint),
                headers=await self._headers(),
            )

            response.raise_for_status()

        except httpx.HTTPError as exc:
            raise MicrosoftGraphClientError(
                f"Microsoft Graph DELETE failed: {endpoint}"
            ) from exc

    async def download(
        self,
        endpoint: str,
    ) -> bytes:
        try:
            response = await self._client.get(
                self._url(endpoint),
                headers=await self._headers(),
            )

            response.raise_for_status()

            return response.content

        except httpx.HTTPError as exc:
            raise MicrosoftGraphClientError(
                f"Microsoft Graph download failed: {endpoint}"
            ) from exc

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> MicrosoftGraphClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        await self.close()
        
    async def download_stream(
        self,
        endpoint: str,
        chunk_size: int = 1024 * 1024,
    ) -> AsyncIterator[bytes]:

        try:
            async with self._client.stream(
                "GET",
                self._url(endpoint),
                headers=await self._headers(),
            ) as response:

                response.raise_for_status()

                async for chunk in response.aiter_bytes(
                    chunk_size=chunk_size,
                ):
                    if chunk:
                        yield chunk

        except httpx.HTTPError as exc:
            raise MicrosoftGraphClientError(
                f"Microsoft Graph stream download failed: {endpoint}"
            ) from exc