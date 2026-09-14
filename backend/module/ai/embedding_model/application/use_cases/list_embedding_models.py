from module.ai.embedding_model.domain.contracts.embedding_model_repository import (
    EmbeddingModelRepository,
)
from module.ai.embedding_model.domain.entities.embedding_model import (
    EmbeddingModel,
)


class ListEmbeddingModelsUseCase:

    def __init__(
        self,
        repository: EmbeddingModelRepository,
    ):
        self.repository = repository

    async def execute(
        self,
    ) -> list[EmbeddingModel]:

        return await self.repository.list_enabled()
