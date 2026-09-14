from module.knowledge_space.domain.contracts.knowledge_space_embedding_config_repository import (
    KnowledgeSpaceEmbeddingConfigRepository,
)
from module.knowledge_space.domain.entities.knowledge_space_embedding_config import (
    KnowledgeSpaceEmbeddingConfig,
)


class SaveKnowledgeSpaceEmbeddingConfigUseCase:

    def __init__(
        self,
        repository: KnowledgeSpaceEmbeddingConfigRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        config: KnowledgeSpaceEmbeddingConfig,
    ) -> KnowledgeSpaceEmbeddingConfig:

        return await self.repository.upsert(
            config,
        )
