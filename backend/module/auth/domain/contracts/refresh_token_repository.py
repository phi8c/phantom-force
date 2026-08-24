from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from datetime import datetime
from uuid import UUID

from module.auth.domain.entities.refresh_token import RefreshToken


class RefreshTokenRepository(
    ABC,
):

    @abstractmethod
    async def get_by_token_hash(
        self,
        token_hash: str,
    ) -> RefreshToken | None:
        pass

    @abstractmethod
    async def add(
        self,
        entity: RefreshToken,
    ) -> RefreshToken:
        pass

    @abstractmethod
    async def update(
        self,
        entity: RefreshToken,
    ) -> None:
        pass

    @abstractmethod
    async def revoke_all_by_session_id(
        self,
        session_id: UUID,
        revoked_at: datetime,
    ) -> None:
        pass