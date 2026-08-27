from abc import ABC
from abc import abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class ExtractedDocument:
    document_id: UUID
    content_path: Path


@dataclass(frozen=True)
class Chunk:
    index: int
    title: str | None
    content: str
    metadata: dict[str, Any]


class ChunkingEngine(ABC):

    @abstractmethod
    def chunk(
        self,
        document: ExtractedDocument,
    ) -> Iterable[Chunk]:
        pass
