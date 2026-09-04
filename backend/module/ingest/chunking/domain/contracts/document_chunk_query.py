from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class DocumentChunkRecord:
    id: UUID
    content: str
    metadata: dict[str, Any]


class DocumentChunkQuery(ABC):

    @abstractmethod
    async def list_by_batch_id(
        self,
        batch_id: UUID,
    ) -> list[DocumentChunkRecord]:
        pass
