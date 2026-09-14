from abc import ABC
from abc import abstractmethod
from uuid import UUID

from module.knowledge_space.domain.entities.knowledge_space_data_hub import (
    KnowledgeSpaceDataHub,
)


class KnowledgeSpaceDataHubRepository(ABC):

    @abstractmethod
    async def get_by_knowledge_space_id(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpaceDataHub | None:
        pass

    @abstractmethod
    async def upsert(
        self,
        config: KnowledgeSpaceDataHub,
    ) -> KnowledgeSpaceDataHub:
        pass
