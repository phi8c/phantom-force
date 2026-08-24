from abc import ABC
from abc import abstractmethod
from uuid import UUID

from app.domain.entities.chunk_batch import (
    ChunkBatch,
)


class ChunkBatchRepository(
    ABC,
):

    @abstractmethod
    async def create(
        self,
        batch: ChunkBatch,
    ) -> ChunkBatch:
        ...

    @abstractmethod
    async def get_by_id(
        self,
        batch_id: UUID,
    ) -> ChunkBatch | None:
        ...

    @abstractmethod
    async def list_by_document_id(
        self,
        document_id: UUID,
    ) -> list[ChunkBatch]:
        ...
    
    @abstractmethod
    async def mark_classification_completed(
        self,
        batch_id: UUID,
    ) -> None:
        ...


    @abstractmethod
    async def mark_embedding_completed(
        self,
        batch_id: UUID,
    ) -> None:
        ...


    @abstractmethod
    async def try_complete_batch(
        self,
        batch_id: UUID,
    ) -> bool:
        ...