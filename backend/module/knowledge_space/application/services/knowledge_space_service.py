from uuid import UUID

from module.knowledge_space.application.use_cases.get_data_hub_config import (
    GetKnowledgeSpaceDataHubUseCase,
)
from module.knowledge_space.application.use_cases.get_embedding_config import (
    GetKnowledgeSpaceEmbeddingConfigUseCase,
)
from module.knowledge_space.application.use_cases.get_knowledge_space import (
    GetKnowledgeSpaceUseCase,
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


class KnowledgeSpaceService:

    def __init__(
        self,
        get_knowledge_space: GetKnowledgeSpaceUseCase,
        get_data_hub_config: GetKnowledgeSpaceDataHubUseCase,
        get_embedding_config: GetKnowledgeSpaceEmbeddingConfigUseCase,
    ):
        self._get_knowledge_space = (
            get_knowledge_space
        )

        self._get_data_hub_config = (
            get_data_hub_config
        )

        self._get_embedding_config = (
            get_embedding_config
        )

    async def get_knowledge_space(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpace | None:

        return await self._get_knowledge_space.execute(
            knowledge_space_id,
        )

    async def get_data_hub_config(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpaceDataHub | None:

        return await self._get_data_hub_config.execute(
            knowledge_space_id,
        )

    async def get_embedding_config(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpaceEmbeddingConfig | None:

        return await self._get_embedding_config.execute(
            knowledge_space_id,
        )