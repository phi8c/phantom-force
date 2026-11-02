from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from module.auth.domain.contracts.auth_session_repository import (
    AuthSessionRepository,
)
from module.auth.domain.entities.auth_session import (
    AuthSession,
)

from module.auth.infrastructure.persistence.mappers.auth_session_mapper import (
    AuthSessionMapper,
)
from module.auth.infrastructure.persistence.models.auth_session_model import (
    AuthSessionModel,
)

from shared.repositories.base_repository import (
    BaseRepository,
)


class AuthSessionRepositoryImpl(
    BaseRepository[AuthSessionModel],
    AuthSessionRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(
            session=session,
            model=AuthSessionModel,
        )

    async def get_by_token_hash(
        self,
        session_token_hash: str,
    ) -> AuthSession | None:

        result = await self.session.execute(
            select(
                AuthSessionModel,
            ).where(
                AuthSessionModel.session_token_hash == session_token_hash,
            ),
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return AuthSessionMapper.to_domain(
            model,
        )

    async def add(
        self,
        entity: AuthSession,
    ) -> AuthSession:

        model = AuthSessionMapper.to_model(
            entity,
        )

        model = await super().add(
            model,
        )

        return AuthSessionMapper.to_domain(
            model,
        )

    async def update(
        self,
        entity: AuthSession,
    ) -> None:

        result = await self.session.execute(
            update(AuthSessionModel)
            .where(AuthSessionModel.id == entity.id)
            .values(
                last_seen_at=entity.last_seen_at,
                idle_expires_at=entity.idle_expires_at,
                mfa_verified_at=entity.mfa_verified_at,
                revoked_at=entity.revoked_at,
                revoked_reason=entity.revoked_reason,
            )
        )
        if result.rowcount == 0:
            raise ValueError(
                "AuthSession not found",
            )

    async def list_active_by_user_id(
        self,
        user_id: UUID,
    ) -> list[AuthSession]:

        result = await self.session.execute(
            select(
                AuthSessionModel,
            ).where(
                AuthSessionModel.user_id == user_id,
                AuthSessionModel.revoked_at.is_(
                    None,
                ),
            ),
        )

        return [
            AuthSessionMapper.to_domain(
                model,
            )
            for model in result.scalars().all()
        ]

    async def revoke_all_by_user_id(
        self,
        user_id: UUID,
        revoked_at: datetime,
        revoked_reason: str,
    ) -> None:

        await self.session.execute(
            update(AuthSessionModel)
            .where(
                AuthSessionModel.user_id == user_id,
                AuthSessionModel.revoked_at.is_(
                    None,
                ),
            )
            .values(
                revoked_at=revoked_at,
                revoked_reason=revoked_reason,
            )
        )
