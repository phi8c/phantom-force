from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.auth.domain.contracts.verification_token_repository import (
    VerificationTokenRepository,
)
from module.auth.domain.entities.verification_token import (
    VerificationToken,
)
from module.auth.domain.enums.token_purpose import (
    TokenPurpose,
)

from module.auth.infrastructure.persistence.mappers.verification_token_mapper import (
    VerificationTokenMapper,
)
from module.auth.infrastructure.persistence.models.verification_token_model import (
    VerificationTokenModel,
)

from app.shared.repositories.base_repository import (
    BaseRepository,
)


class VerificationTokenRepositoryImpl(
    BaseRepository[VerificationTokenModel],
    VerificationTokenRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(
            session=session,
            model=VerificationTokenModel,
        )

    async def get_by_token_hash(
        self,
        token_hash: str,
    ) -> VerificationToken | None:

        result = await self.session.execute(
            select(
                VerificationTokenModel,
            ).where(
                VerificationTokenModel.token_hash == token_hash,
            ),
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return VerificationTokenMapper.to_domain(
            model,
        )

    async def add(
        self,
        entity: VerificationToken,
    ) -> VerificationToken:

        model = VerificationTokenMapper.to_model(
            entity,
        )

        model = await super().add(
            model,
        )

        return VerificationTokenMapper.to_domain(
            model,
        )

    async def update(
        self,
        entity: VerificationToken,
    ) -> None:

        model = await super().get_by_id(
            entity.id,
        )

        if model is None:
            raise ValueError(
                "VerificationToken not found",
            )

        model.used_at = entity.used_at

        await self.session.flush()

    async def invalidate_active_by_user_and_purpose(
        self,
        user_id: UUID,
        purpose: TokenPurpose,
        used_at: datetime,
    ) -> None:
        """
        Goi truoc khi phat token moi (vd request_password_reset lan 2) - vo hieu
        hoa moi token cung purpose chua dung, tranh nhieu token active cung luc
        cho cung 1 muc dich.
        """

        result = await self.session.execute(
            select(
                VerificationTokenModel,
            ).where(
                VerificationTokenModel.user_id == user_id,
                VerificationTokenModel.purpose == purpose.value,
                VerificationTokenModel.used_at.is_(
                    None,
                ),
            ),
        )

        for model in result.scalars().all():
            model.used_at = used_at

        await self.session.flush()