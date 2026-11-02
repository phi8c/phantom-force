from abc import ABC
from abc import abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class DocumentChunkRecord:
    id: UUID
    content: str
    metadata: dict[str, Any]


class DocumentChunkQuery(ABC):

    async def iter_by_batch_id(self, batch_id: UUID, *, page_size: int = 32) -> AsyncIterator[list[DocumentChunkRecord]]:
        if page_size < 1:
            raise ValueError('Page size must be positive')
        chunks = await self.list_by_batch_id(batch_id)
        for start in range(0, len(chunks), page_size):
            yield chunks[start:start + page_size]

    @abstractmethod
    async def list_by_batch_id(
        self,
        batch_id: UUID,
    ) -> list[DocumentChunkRecord]:
        pass
