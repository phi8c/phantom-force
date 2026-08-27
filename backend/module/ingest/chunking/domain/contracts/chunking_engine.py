from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class ExtractedDocument:
    document_id: UUID
    content: dict[str, Any]


@dataclass(frozen=True)
class Chunk:
    index: int
    title: str | None
    content: str
    metadata: dict[str, Any]


class ChunkingEngine(ABC):

    @abstractmethod
    async def chunk(
        self,
        document: ExtractedDocument,
    ) -> list[Chunk]:
        pass
