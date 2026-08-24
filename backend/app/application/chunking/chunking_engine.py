from collections.abc import Iterator

from app.application.chunking.contracts.chunk_strategy import (
    ChunkStrategy,
)

from app.domain.entities.chunk import (
    Chunk,
)

from app.domain.entities.document_extraction import (
    DocumentExtraction,
)


class ChunkingEngine:

    def __init__(
        self,
        strategy: ChunkStrategy,
    ):
        self.strategy = strategy

    def chunk(
        self,
        extraction: DocumentExtraction,
    ) -> Iterator[Chunk]:

        return self.strategy.chunk(
            extraction,
        )