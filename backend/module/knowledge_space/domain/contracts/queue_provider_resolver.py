from abc import ABC, abstractmethod
from uuid import UUID


class QueueProviderResolver(ABC):
    @abstractmethod
    async def resolve(self, knowledge_space_id: UUID) -> str:
        raise NotImplementedError
