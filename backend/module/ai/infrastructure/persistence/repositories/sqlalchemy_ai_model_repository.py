from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ai.domain.contracts.ai_model_repository import (
    AIModelRepository,
)
from module.ai.domain.entities.ai_model import (
    AIModel,
)
from module.ai.infrastructure.persistence.mappers.ai_model_mapper import (
    AIModelMapper,
)
from module.ai.infrastructure.persistence.models.ai_model_model import (
    AIModelModel,
)
from module.ai.infrastructure.persistence.models.ai_provider_model import (
    AIProviderModel,
)
from shared.repositories.base_repository import (
    BaseRepository,
)


class SqlAlchemyAIModelRepository(
    BaseRepository[AIModelModel],
    AIModelRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(
            session=session,
            model=AIModelModel,
        )

    async def get_by_id(
        self,
        model_id: UUID,
    ) -> AIModel | None:

        model = await super().get_by_id(
            model_id,
        )

        if model is None:
            return None

        return AIModelMapper.to_entity(
            model,
        )

    async def get_by_provider_and_code(
        self,
        provider_code: str,
        model_code: str,
    ) -> AIModel | None:

        result = await self.session.execute(
            select(
                AIModelModel,
            )
            .join(
                AIProviderModel,
                AIModelModel.provider_id
                == AIProviderModel.id,
            )
            .where(
                AIProviderModel.code == provider_code,
                AIModelModel.code == model_code,
            ),
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return AIModelMapper.to_entity(
            model,
        )

    async def get_enabled_by_provider_and_code(
        self,
        provider_code: str,
        model_code: str,
    ) -> AIModel | None:

        result = await self.session.execute(
            select(
                AIModelModel,
            )
            .join(
                AIProviderModel,
                AIModelModel.provider_id
                == AIProviderModel.id,
            )
            .where(
                AIProviderModel.code == provider_code,
                AIProviderModel.is_enabled.is_(True),
                AIModelModel.code == model_code,
                AIModelModel.is_enabled.is_(True),
            ),
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return AIModelMapper.to_entity(
            model,
        )

    async def get(
        self,
        provider_code: str,
        model_code: str,
    ) -> AIModel | None:

        return await self.get_enabled_by_provider_and_code(
            provider_code=provider_code,
            model_code=model_code,
        )

    async def list(
        self,
    ) -> list[AIModel]:

        models = await super().get_all()

        return [
            AIModelMapper.to_entity(
                model,
            )
            for model in models
        ]

    async def add(
        self,
        entity: AIModel,
    ) -> AIModel:

        model = AIModelMapper.to_model(
            entity,
        )

        model = await super().add(
            model,
        )

        return AIModelMapper.to_entity(
            model,
        )

    async def update(
        self,
        entity: AIModel,
    ) -> AIModel:

        if entity.id is None:
            raise ValueError(
                "AI model id is required",
            )

        model = await super().get_by_id(
            entity.id,
        )

        if model is None:
            raise ValueError(
                "AI model not found",
            )

        AIModelMapper.merge_into_model(
            model,
            entity,
        )

        await self.session.flush()
        await self.session.refresh(
            model,
        )

        return AIModelMapper.to_entity(
            model,
        )

    async def delete(
        self,
        model_id: UUID,
    ) -> None:

        model = await super().get_by_id(
            model_id,
        )

        if model is None:
            raise ValueError(
                "AI model not found",
            )

        await super().delete(
            model,
        )
