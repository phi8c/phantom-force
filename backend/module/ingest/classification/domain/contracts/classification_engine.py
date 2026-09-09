from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from module.ingest.classification.domain.contracts.chunk_reader import (
    ChunkForClassification,
)
from module.ingest.classification.domain.entities.document_context import (
    DocumentContext,
)


@dataclass(frozen=True)
class ClassificationResult:
    chunk_id: UUID
    model_name: str
    raw_response: dict[str, Any] | None


class ClassificationEngine(ABC):

    @abstractmethod
    async def classify_batch(
        self,
        chunks: list[ChunkForClassification],
        document_context: DocumentContext,
    ) -> list[ClassificationResult]:
        pass
