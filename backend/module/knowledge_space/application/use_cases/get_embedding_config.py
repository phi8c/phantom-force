from uuid import UUID

from module.knowledge_space.domain.contracts.knowledge_space_embedding_config_repository import (
    KnowledgeSpaceEmbeddingConfigRepository,
)
from module.knowledge_space.domain.entities.knowledge_space_embedding_config import (
    KnowledgeSpaceEmbeddingConfig,
)


class GetKnowledgeSpaceEmbeddingConfigUseCase:

    def __init__(
        self,
        repository: KnowledgeSpaceEmbeddingConfigRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpaceEmbeddingConfig | None:

        return await (
            self.repository
            .get_by_knowledge_space_id(
                knowledge_space_id,
            )
        )