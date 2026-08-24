from uuid import UUID

from module.knowledge_space.domain.contracts.knowledge_space_repository import (
    KnowledgeSpaceRepository,
)
from module.knowledge_space.domain.entities.knowledge_space import (
    KnowledgeSpace,
)


class GetKnowledgeSpaceUseCase:

    def __init__(
        self,
        repository: KnowledgeSpaceRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpace | None:

        return await self.repository.get_by_id(
            knowledge_space_id,
        )