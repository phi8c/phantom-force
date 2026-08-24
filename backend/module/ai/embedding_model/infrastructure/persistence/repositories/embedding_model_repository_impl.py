from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ai.embedding_model.domain.contracts.embedding_model_repository import (
    EmbeddingModelRepository,
)
from module.ai.embedding_model.domain.entities.embedding_model import (
    EmbeddingModel,
)
from module.ai.embedding_model.infrastructure.persistence.mappers.embedding_model_mapper import (
    EmbeddingModelMapper,
)
from module.ai.embedding_model.infrastructure.persistence.models.embedding_model_model import (
    EmbeddingModelModel,
)


class EmbeddingModelRepositoryImpl(
    EmbeddingModelRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_id(
        self,
        embedding_model_id: UUID,
    ) -> EmbeddingModel | None:

        result = await self.session.execute(
            select(
                EmbeddingModelModel,
            ).where(
                EmbeddingModelModel.id
                == embedding_model_id,
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return EmbeddingModelMapper.to_entity(
            model,
        )

    async def get_by_code(
        self,
        code: str,
    ) -> EmbeddingModel | None:

        result = await self.session.execute(
            select(
                EmbeddingModelModel,
            ).where(
                EmbeddingModelModel.code
                == code,
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return EmbeddingModelMapper.to_entity(
            model,
        )