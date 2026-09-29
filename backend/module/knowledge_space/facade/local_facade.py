from uuid import UUID

from module.knowledge_space.domain.contracts.knowledge_space_repository import (
    KnowledgeSpaceRepository,
)
from module.knowledge_space.facade.contract import KnowledgeSpaceModuleFacade
from module.knowledge_space.facade.dto import KnowledgeSpaceDTO


class LocalKnowledgeSpaceFacade(KnowledgeSpaceModuleFacade):
    def __init__(self, repository: KnowledgeSpaceRepository):
        self._repository = repository

    async def get_knowledge_space(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpaceDTO | None:
        knowledge_space = await self._repository.get_by_id(knowledge_space_id)
        if knowledge_space is None or knowledge_space.id is None:
            return None
        return KnowledgeSpaceDTO(
            id=knowledge_space.id,
            status=knowledge_space.status,
        )
