from abc import ABC
from abc import abstractmethod
from collections.abc import Iterator

from module.ingest.chunking.engine.models.chunk import (
    Chunk,
)

from module.ingest.chunking.engine.models.document_extraction import (
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
