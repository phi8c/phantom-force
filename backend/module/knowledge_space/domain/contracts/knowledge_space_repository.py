from abc import ABC
from abc import abstractmethod
from uuid import UUID

from module.knowledge_space.domain.entities.knowledge_space import (
    KnowledgeSpace,
)
from module.knowledge_space.domain.entities.knowledge_space_list_item import (
    KnowledgeSpaceListItem,
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

    @abstractmethod
    async def create(
        self,
        knowledge_space: KnowledgeSpace,
    ) -> KnowledgeSpace:
        pass

    @abstractmethod
    async def list_page(
        self,
        *,
        limit: int,
        offset: int,
        enterprise_id: UUID | None = None,
        search: str | None = None,
        status: str | None = None,
    ) -> tuple[list[KnowledgeSpaceListItem], int]:
        pass
