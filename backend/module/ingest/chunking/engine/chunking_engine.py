from collections.abc import Iterator

from module.ingest.chunking.engine.contracts.chunk_strategy import (
    ChunkStrategy,
)

from module.ingest.chunking.engine.models.chunk import (
    Chunk,
)

from module.ingest.chunking.engine.models.document_extraction import (
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
