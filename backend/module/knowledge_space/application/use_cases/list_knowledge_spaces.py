from uuid import UUID

from module.knowledge_space.domain.contracts.knowledge_space_repository import (
    KnowledgeSpaceRepository,
)
from module.knowledge_space.domain.entities.knowledge_space_list_item import (
    KnowledgeSpaceListItem,
)


class ListKnowledgeSpacesUseCase:

    def __init__(
        self,
        repository: KnowledgeSpaceRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        *,
        limit: int,
        offset: int,
        enterprise_id: UUID | None = None,
        search: str | None = None,
        status: str | None = None,
    ) -> tuple[list[KnowledgeSpaceListItem], int]:

        return await self.repository.list_page(
            limit=limit,
            offset=offset,
            enterprise_id=enterprise_id,
            search=search,
            status=status,
        )
