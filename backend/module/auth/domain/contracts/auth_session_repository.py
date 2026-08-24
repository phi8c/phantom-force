from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from datetime import datetime
from uuid import UUID

from module.auth.domain.entities.auth_session import AuthSession


class AuthSessionRepository(
    ABC,
):

    @abstractmethod
    async def get_by_token_hash(
        self,
        session_token_hash: str,
    ) -> AuthSession | None:
        pass

    @abstractmethod
    async def add(
        self,
        entity: AuthSession,
    ) -> AuthSession:
        pass

    @abstractmethod
    async def update(
        self,
        entity: AuthSession,
    ) -> None:
        pass

    @abstractmethod
    async def list_active_by_user_id(
        self,
        user_id: UUID,
    ) -> list[AuthSession]:
        pass

    @abstractmethod
    async def revoke_all_by_user_id(
        self,
        user_id: UUID,
        revoked_at: datetime,
        revoked_reason: str,
    ) -> None:
        pass