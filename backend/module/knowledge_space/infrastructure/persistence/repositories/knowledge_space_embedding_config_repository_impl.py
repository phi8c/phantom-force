from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.knowledge_space.domain.contracts.knowledge_space_embedding_config_repository import (
    KnowledgeSpaceEmbeddingConfigRepository,
)
from module.knowledge_space.domain.entities.knowledge_space_embedding_config import (
    KnowledgeSpaceEmbeddingConfig,
)
from module.knowledge_space.infrastructure.persistence.mappers.knowledge_space_embedding_config_mapper import (
    KnowledgeSpaceEmbeddingConfigMapper,
)
from module.knowledge_space.infrastructure.persistence.models.knowledge_space_embedding_config_model import (
    KnowledgeSpaceEmbeddingConfigModel,
)


class KnowledgeSpaceEmbeddingConfigRepositoryImpl(
    KnowledgeSpaceEmbeddingConfigRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_knowledge_space_id(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpaceEmbeddingConfig | None:

        result = await self.session.execute(
            select(
                KnowledgeSpaceEmbeddingConfigModel,
            ).where(
                KnowledgeSpaceEmbeddingConfigModel.knowledge_space_id
                == knowledge_space_id,
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return (
            KnowledgeSpaceEmbeddingConfigMapper.to_entity(
                model,
            )
        )

    async def upsert(
        self,
        config: KnowledgeSpaceEmbeddingConfig,
    ) -> KnowledgeSpaceEmbeddingConfig:

        result = await self.session.execute(
            select(
                KnowledgeSpaceEmbeddingConfigModel,
            ).where(
                KnowledgeSpaceEmbeddingConfigModel.knowledge_space_id
                == config.knowledge_space_id,
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            model = KnowledgeSpaceEmbeddingConfigModel(
                knowledge_space_id=config.knowledge_space_id,
                embedding_model_id=config.embedding_model_id,
                configuration=config.configuration,
                enabled=config.enabled,
            )
            self.session.add(
                model,
            )
        else:
            model.embedding_model_id = config.embedding_model_id
            model.configuration = config.configuration
            model.enabled = config.enabled

        await self.session.flush()
        await self.session.refresh(
            model,
        )

        return (
            KnowledgeSpaceEmbeddingConfigMapper.to_entity(
                model,
            )
        )
