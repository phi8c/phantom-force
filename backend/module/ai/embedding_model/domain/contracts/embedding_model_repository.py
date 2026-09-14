from abc import ABC
from abc import abstractmethod
from uuid import UUID

from module.ai.embedding_model.domain.entities.embedding_model import (
    EmbeddingModel,
)


class EmbeddingModelRepository(ABC):

    @abstractmethod
    async def get_by_id(
        self,
        embedding_model_id: UUID,
    ) -> EmbeddingModel | None:
        pass

    @abstractmethod
    async def get_by_code(
        self,
        code: str,
    ) -> EmbeddingModel | None:
        pass

    @abstractmethod
    async def list_enabled(
        self,
    ) -> list[EmbeddingModel]:
        pass
