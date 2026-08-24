from abc import ABC
from abc import abstractmethod
from uuid import UUID

from module.knowledge_space.domain.entities.knowledge_space import (
    KnowledgeSpace,
)


class KnowledgeSpaceRepository(ABC):

    @abstractmethod
    async def get_by_id(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpace | None:
        pass

    @abstractmethod
    async def get_by_code(
        self,
        code: str,
    ) -> KnowledgeSpace | None:
        pass