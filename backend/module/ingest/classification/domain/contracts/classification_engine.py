from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from module.ingest.classification.domain.contracts.chunk_reader import (
    ChunkForClassification,
)


@dataclass(frozen=True)
class ClassificationResult:
    chunk_id: UUID
    sensitivity: int
    metadata: dict[str, Any]


class ClassificationEngine(ABC):

    @abstractmethod
    async def classify_batch(
        self,
        chunks: list[ChunkForClassification],
    ) -> list[ClassificationResult]:
        pass
