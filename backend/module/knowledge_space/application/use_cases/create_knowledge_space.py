from module.knowledge_space.domain.contracts.knowledge_space_repository import (
    KnowledgeSpaceRepository,
)
from module.knowledge_space.domain.entities.knowledge_space import (
    KnowledgeSpace,
)


class CreateKnowledgeSpaceUseCase:

    def __init__(
        self,
        repository: KnowledgeSpaceRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        knowledge_space: KnowledgeSpace,
    ) -> KnowledgeSpace:

        return await self.repository.create(
            knowledge_space,
        )
