from module.knowledge_space.domain.contracts.knowledge_space_data_hub_repository import (
    KnowledgeSpaceDataHubRepository,
)
from module.knowledge_space.domain.entities.knowledge_space_data_hub import (
    KnowledgeSpaceDataHub,
)


class SaveKnowledgeSpaceDataHubConfigUseCase:

    def __init__(
        self,
        repository: KnowledgeSpaceDataHubRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        config: KnowledgeSpaceDataHub,
    ) -> KnowledgeSpaceDataHub:

        return await self.repository.upsert(
            config,
        )
