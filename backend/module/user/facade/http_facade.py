from __future__ import annotations

from uuid import UUID

import httpx

from .contract import UserModuleFacade
from .dto import UserDTO


class HttpUserFacade(
    UserModuleFacade,
):
    """
    Impl goi qua HTTP - dung khi module user da tach thanh microservice
    rieng. Goi vao prefix /internal/* (khong public), xac thuc bang HMAC
    header giua cac module - KHONG dung session cookie cua user.
    """

    def __init__(
        self,
        base_url: str,
        service_secret: str,
        client: httpx.AsyncClient,
    ):
        self._base_url = base_url
        self._service_secret = service_secret
        self._client = client

    def _headers(
        self,
    ) -> dict[str, str]:

        return {
            "X-Internal-Service-Secret": self._service_secret,
        }

    async def get_user(
        self,
        user_id: UUID,
    ) -> UserDTO | None:

        response = await self._client.get(
            f"{self._base_url}/internal/users/{user_id}",
            headers=self._headers(),
        )

        if response.status_code == 404:
            return None

        response.raise_for_status()

        return UserDTO(
            **response.json(),
        )

    async def get_user_by_email(
        self,
        email: str,
    ) -> UserDTO | None:

        response = await self._client.get(
            f"{self._base_url}/internal/users",
            params={
                "email": email,
            },
            headers=self._headers(),
        )

        if response.status_code == 404:
            return None

        response.raise_for_status()

        return UserDTO(
            **response.json(),
        )

    async def create_user(
        self,
        email: str,
    ) -> UserDTO:

        response = await self._client.post(
            f"{self._base_url}/internal/users",
            json={
                "email": email,
            },
            headers=self._headers(),
        )

        response.raise_for_status()

        return UserDTO(
            **response.json(),
        )

    async def mark_email_verified(
        self,
        user_id: UUID,
    ) -> None:

        response = await self._client.post(
            f"{self._base_url}/internal/users/{user_id}/verify-email",
            headers=self._headers(),
        )

        response.raise_for_status()