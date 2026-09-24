from abc import ABC, abstractmethod
from uuid import UUID

from ..entities.knowledge_space_queue import KnowledgeSpaceQueue


class KnowledgeSpaceQueueRepository(ABC):
    @abstractmethod
    async def get_default_for_knowledge_space(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpaceQueue | None:
        """Return the configured default mapping without filtering disabled rows."""
        raise NotImplementedError
