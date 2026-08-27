from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.auth.domain.contracts.refresh_token_repository import (
    RefreshTokenRepository,
)
from module.auth.domain.entities.refresh_token import (
    RefreshToken,
)

from module.auth.infrastructure.persistence.mappers.refresh_token_mapper import (
    RefreshTokenMapper,
)
from module.auth.infrastructure.persistence.models.refresh_token_model import (
    RefreshTokenModel,
)

from shared.repositories.base_repository import (
    BaseRepository,
)


class RefreshTokenRepositoryImpl(
    BaseRepository[RefreshTokenModel],
    RefreshTokenRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(
            session=session,
            model=RefreshTokenModel,
        )

    async def get_by_token_hash(
        self,
        token_hash: str,
    ) -> RefreshToken | None:

        result = await self.session.execute(
            select(
                RefreshTokenModel,
            ).where(
                RefreshTokenModel.token_hash == token_hash,
            ),
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return RefreshTokenMapper.to_domain(
            model,
        )

    async def add(
        self,
        entity: RefreshToken,
    ) -> RefreshToken:

        model = RefreshTokenMapper.to_model(
            entity,
        )

        model = await super().add(
            model,
        )

        return RefreshTokenMapper.to_domain(
            model,
        )

    async def update(
        self,
        entity: RefreshToken,
    ) -> None:

        model = await super().get_by_id(
            entity.id,
        )

        if model is None:
            raise ValueError(
                "RefreshToken not found",
            )

        model.used_at = entity.used_at
        model.revoked_at = entity.revoked_at
        model.replaced_by = entity.replaced_by

        await self.session.flush()

    async def revoke_all_by_session_id(
        self,
        session_id: UUID,
        revoked_at: datetime,
    ) -> None:
        """
        Dung khi phat hien refresh token reuse (token da used_at nhung bi dung
        lai) - revoke toan bo "family" thuoc cung 1 session, khong chi 1 token.
        """

        result = await self.session.execute(
            select(
                RefreshTokenModel,
            ).where(
                RefreshTokenModel.session_id == session_id,
                RefreshTokenModel.revoked_at.is_(
                    None,
                ),
            ),
        )

        for model in result.scalars().all():
            model.revoked_at = revoked_at

        await self.session.flush()