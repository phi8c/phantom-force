from abc import ABC
from abc import abstractmethod
from collections.abc import Iterable
from uuid import UUID

from module.ingest.classification.domain.entities.chunk_classification import (
    ChunkClassification,
)


class ChunkClassificationRepository(ABC):

    @abstractmethod
    async def list_by_batch_id(
        self,
        batch_id: UUID,
    ) -> list[ChunkClassification]:
        pass

    @abstractmethod
    async def upsert_many(
        self,
        classifications: Iterable[ChunkClassification],
    ) -> list[ChunkClassification]:
        pass
