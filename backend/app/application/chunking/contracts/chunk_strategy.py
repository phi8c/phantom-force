from abc import ABC
from abc import abstractmethod
from collections.abc import Iterator

from app.domain.entities.chunk import (
    Chunk,
)

from app.domain.entities.document_extraction import (
    DocumentExtraction,
)


class ChunkStrategy(
    ABC,
):

    @abstractmethod
    def chunk(
        self,
        extraction: DocumentExtraction,
    ) -> Iterator[Chunk]:
        pass