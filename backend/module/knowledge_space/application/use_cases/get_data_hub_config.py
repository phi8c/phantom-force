from uuid import UUID

from module.knowledge_space.domain.contracts.knowledge_space_data_hub_repository import (
    KnowledgeSpaceDataHubRepository,
)
from module.knowledge_space.domain.entities.knowledge_space_data_hub import (
    KnowledgeSpaceDataHub,
)


class GetKnowledgeSpaceDataHubUseCase:

    def __init__(
        self,
        repository: KnowledgeSpaceDataHubRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpaceDataHub | None:

        return await (
            self.repository
            .get_by_knowledge_space_id(
                knowledge_space_id,
            )
        )