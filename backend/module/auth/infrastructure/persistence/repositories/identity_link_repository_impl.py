from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.auth.domain.contracts.identity_link_repository import (
    IdentityLinkRepository,
)


from module.auth.domain.entities.identity_link import (
    IdentityLink,
)
from module.auth.domain.enums.auth_provider import (
    AuthProvider,
)

from module.auth.infrastructure.persistence.mappers.identity_link_mapper import (
    IdentityLinkMapper,
)
from module.auth.infrastructure.persistence.models.identity_link_model import (
    IdentityLinkModel,
)

from app.shared.repositories.base_repository import (
    BaseRepository,
)


class IdentityLinkRepositoryImpl(
    BaseRepository[IdentityLinkModel],
    IdentityLinkRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(
            session=session,
            model=IdentityLinkModel,
        )

    async def get_by_provider_and_sub(
        self,
        provider: AuthProvider,
        external_sub: str,
    ) -> IdentityLink | None:

        result = await self.session.execute(
            select(
                IdentityLinkModel,
            ).where(
                IdentityLinkModel.provider == provider.value,
                IdentityLinkModel.external_sub == external_sub,
            ),
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return IdentityLinkMapper.to_domain(
            model,
        )

    async def list_by_user_id(
        self,
        user_id: UUID,
    ) -> list[IdentityLink]:

        result = await self.session.execute(
            select(
                IdentityLinkModel,
            ).where(
                IdentityLinkModel.user_id == user_id,
            ),
        )

        return [
            IdentityLinkMapper.to_domain(
                model,
            )
            for model in result.scalars().all()
        ]

    async def add(
        self,
        entity: IdentityLink,
    ) -> IdentityLink:

        model = IdentityLinkMapper.to_model(
            entity,
        )

        model = await super().add(
            model,
        )

        return IdentityLinkMapper.to_domain(
            model,
        )