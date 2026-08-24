from uuid import UUID

from module.ai.embedding_model.application.use_cases.get_embedding_model import (
    GetEmbeddingModelUseCase,
)
from module.ai.embedding_model.application.use_cases.get_embedding_model_by_code import (
    GetEmbeddingModelByCodeUseCase,
)
from module.ai.embedding_model.domain.entities.embedding_model import (
    EmbeddingModel,
)


class EmbeddingModelService:

    def __init__(
        self,
        get_embedding_model: GetEmbeddingModelUseCase,
        get_embedding_model_by_code: GetEmbeddingModelByCodeUseCase,
    ):
        self._get_embedding_model = (
            get_embedding_model
        )
        self._get_embedding_model_by_code = (
            get_embedding_model_by_code
        )

    async def get_by_id(
        self,
        embedding_model_id: UUID,
    ) -> EmbeddingModel | None:

        return await self._get_embedding_model.execute(
            embedding_model_id,
        )

    async def get_by_code(
        self,
        code: str,
    ) -> EmbeddingModel | None:

        return await (
            self._get_embedding_model_by_code.execute(
                code,
            )
        )