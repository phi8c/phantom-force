from abc import ABC
from abc import abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

from module.ingest.classification.application.dtos.schemas.schemas import Chunk


@dataclass(slots=True)
class ClassificationResult:
    chunk_id: str
    sensitivity: int
    metadata: dict


class ClassificationEngine(ABC):

    @abstractmethod
    async def classify(
        self,
        chunks: Sequence[Chunk],
    ) -> Sequence[ClassificationResult]:
        """
        Classify sensitivity for a batch of chunks.

        sensitivity:
            1 = PUBLIC
            Higher values represent higher sensitivity levels.
        """
        raise NotImplementedError