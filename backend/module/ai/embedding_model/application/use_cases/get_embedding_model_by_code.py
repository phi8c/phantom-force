from module.ai.embedding_model.domain.contracts.embedding_model_repository import (
    EmbeddingModelRepository,
)
from module.ai.embedding_model.domain.entities.embedding_model import (
    EmbeddingModel,
)


class GetEmbeddingModelByCodeUseCase:

    def __init__(
        self,
        repository: EmbeddingModelRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        code: str,
    ) -> EmbeddingModel | None:

        return await self.repository.get_by_code(
            code,
        )