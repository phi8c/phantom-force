from abc import ABC
from abc import abstractmethod
from uuid import UUID

from module.knowledge_space.domain.entities.knowledge_space_embedding_config import (
    KnowledgeSpaceEmbeddingConfig,
)


class KnowledgeSpaceEmbeddingConfigRepository(ABC):

    @abstractmethod
    async def get_by_knowledge_space_id(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpaceEmbeddingConfig | None:
        pass