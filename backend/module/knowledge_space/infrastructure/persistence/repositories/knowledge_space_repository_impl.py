from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.knowledge_space.domain.contracts.knowledge_space_data_hub_repository import (
    KnowledgeSpaceDataHubRepository,
)
from module.knowledge_space.domain.contracts.knowledge_space_embedding_config_repository import (
    KnowledgeSpaceEmbeddingConfigRepository,
)
from module.knowledge_space.domain.contracts.knowledge_space_repository import (
    KnowledgeSpaceRepository,
)

from module.knowledge_space.domain.entities.knowledge_space import (
    KnowledgeSpace,
)
from module.knowledge_space.domain.entities.knowledge_space_data_hub import (
    KnowledgeSpaceDataHub,
)
from module.knowledge_space.domain.entities.knowledge_space_embedding_config import (
    KnowledgeSpaceEmbeddingConfig,
)

from module.knowledge_space.infrastructure.persistence.mappers.knowledge_space_data_hub_mapper import (
    KnowledgeSpaceDataHubMapper,
)
from module.knowledge_space.infrastructure.persistence.mappers.knowledge_space_embedding_config_mapper import (
    KnowledgeSpaceEmbeddingConfigMapper,
)
from module.knowledge_space.infrastructure.persistence.mappers.knowledge_space_mapper import (
    KnowledgeSpaceMapper,
)

from module.knowledge_space.infrastructure.persistence.models.knowledge_space_data_hub_model import (
    KnowledgeSpaceDataHubModel,
)
from module.knowledge_space.infrastructure.persistence.models.knowledge_space_embedding_config_model import (
    KnowledgeSpaceEmbeddingConfigModel,
)
from module.knowledge_space.infrastructure.persistence.models.knowledge_space_model import (
    KnowledgeSpaceModel,
)


class KnowledgeSpaceRepositoryImpl(
    KnowledgeSpaceRepository,
    KnowledgeSpaceDataHubRepository,
    KnowledgeSpaceEmbeddingConfigRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_id(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpace | None:

        result = await self.session.execute(
            select(
                KnowledgeSpaceModel,
            ).where(
                KnowledgeSpaceModel.id
                == knowledge_space_id,
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return KnowledgeSpaceMapper.to_entity(
            model,
        )

    async def get_by_code(
        self,
        code: str,
    ) -> KnowledgeSpace | None:

        result = await self.session.execute(
            select(
                KnowledgeSpaceModel,
            ).where(
                KnowledgeSpaceModel.code
                == code,
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return KnowledgeSpaceMapper.to_entity(
            model,
        )

    async def get_by_knowledge_space_id(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpaceDataHub | KnowledgeSpaceEmbeddingConfig | None:

        raise NotImplementedError