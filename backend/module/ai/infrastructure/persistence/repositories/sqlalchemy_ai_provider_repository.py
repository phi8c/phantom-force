from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ai.domain.contracts.ai_provider_repository import (
    AIProviderRepository,
)
from module.ai.domain.entities.ai_provider import (
    AIProvider,
)
from module.ai.infrastructure.persistence.mappers.ai_provider_mapper import (
    AIProviderMapper,
)
from module.ai.infrastructure.persistence.models.ai_provider_model import (
    AIProviderModel,
)
from shared.repositories.base_repository import (
    BaseRepository,
)


class SqlAlchemyAIProviderRepository(
    BaseRepository[AIProviderModel],
    AIProviderRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(
            session=session,
            model=AIProviderModel,
        )

    async def get_by_id(
        self,
        provider_id: UUID,
    ) -> AIProvider | None:

        model = await super().get_by_id(
            provider_id,
        )

        if model is None:
            return None

        return AIProviderMapper.to_entity(
            model,
        )

    async def get_by_code(
        self,
        code: str,
    ) -> AIProvider | None:

        result = await self.session.execute(
            select(
                AIProviderModel,
            ).where(
                AIProviderModel.code == code,
            ),
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return AIProviderMapper.to_entity(
            model,
        )

    async def get_enabled_by_code(
        self,
        code: str,
    ) -> AIProvider | None:

        result = await self.session.execute(
            select(
                AIProviderModel,
            ).where(
                AIProviderModel.code == code,
                AIProviderModel.is_enabled.is_(True),
            ),
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return AIProviderMapper.to_entity(
            model,
        )

    async def list(
        self,
    ) -> list[AIProvider]:

        models = await super().get_all()

        return [
            AIProviderMapper.to_entity(
                model,
            )
            for model in models
        ]

    async def add(
        self,
        entity: AIProvider,
    ) -> AIProvider:

        model = AIProviderMapper.to_model(
            entity,
        )

        model = await super().add(
            model,
        )

        return AIProviderMapper.to_entity(
            model,
        )

    async def update(
        self,
        entity: AIProvider,
    ) -> AIProvider:

        if entity.id is None:
            raise ValueError(
                "AI provider id is required",
            )

        model = await super().get_by_id(
            entity.id,
        )

        if model is None:
            raise ValueError(
                "AI provider not found",
            )

        AIProviderMapper.merge_into_model(
            model,
            entity,
        )

        await self.session.flush()
        await self.session.refresh(
            model,
        )

        return AIProviderMapper.to_entity(
            model,
        )

    async def delete(
        self,
        provider_id: UUID,
    ) -> None:

        model = await super().get_by_id(
            provider_id,
        )

        if model is None:
            raise ValueError(
                "AI provider not found",
            )

        await super().delete(
            model,
        )
