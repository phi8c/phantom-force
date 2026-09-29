from abc import ABC, abstractmethod
from uuid import UUID

from module.knowledge_space.facade.dto import KnowledgeSpaceDTO


class KnowledgeSpaceModuleFacade(ABC):
    @abstractmethod
    async def get_knowledge_space(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpaceDTO | None:
        pass
