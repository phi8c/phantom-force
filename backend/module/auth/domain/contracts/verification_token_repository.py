from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from datetime import datetime
from uuid import UUID

from module.auth.domain.entities.verification_token import VerificationToken
from module.auth.domain.enums.token_purpose import TokenPurpose


class VerificationTokenRepository(
    ABC,
):

    @abstractmethod
    async def get_by_token_hash(
        self,
        token_hash: str,
    ) -> VerificationToken | None:
        pass

    @abstractmethod
    async def add(
        self,
        entity: VerificationToken,
    ) -> VerificationToken:
        pass

    @abstractmethod
    async def update(
        self,
        entity: VerificationToken,
    ) -> None:
        pass

    @abstractmethod
    async def invalidate_active_by_user_and_purpose(
        self,
        user_id: UUID,
        purpose: TokenPurpose,
        used_at: datetime,
    ) -> None:
        pass