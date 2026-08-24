from __future__ import annotations

from typing import Literal

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from module.user.infrastructure.persistence.repositories.user_repository_impl import (
    UserRepositoryImpl,
)

from .contract import UserModuleFacade
from .http_facade import HttpUserFacade
from .local_facade import LocalUserFacade

DeploymentMode = Literal["local", "http"]


def get_user_facade(
    mode: DeploymentMode,
    session: AsyncSession | None = None,
    http_base_url: str | None = None,
    http_service_secret: str | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> UserModuleFacade:
    """
    Diem duy nhat quyet dinh Local hay Http - module goi (auth/authz) chi
    Depends() ham nay, khong tu quyet dinh implementation nao duoc dung.
    Doi mode = doi 1 dong config, khong sua code goi noi.
    """

    if mode == "local":

        if session is None:
            raise ValueError(
                "session la bat buoc khi mode='local'",
            )

        return LocalUserFacade(
            user_repository=UserRepositoryImpl(
                session=session,
            ),
        )

    if http_base_url is None or http_service_secret is None or http_client is None:
        raise ValueError(
            "http_base_url, http_service_secret, http_client la bat buoc khi mode='http'",
        )

    return HttpUserFacade(
        base_url=http_base_url,
        service_secret=http_service_secret,
        client=http_client,
    )