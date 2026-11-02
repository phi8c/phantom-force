from module.ingest.chunking.domain.contracts.chunking_engine import ChunkingEngine
from module.ingest.chunking.domain.contracts.document_reader import DocumentReader
from module.ingest.chunking.application.services.block_chunker import BlockChunker
from module.ingest.chunking.application.services.chunk_budget import ChunkBudget
from module.ingest.chunking.infrastructure.reading.indexed_reader import SqliteDocumentReader


class StreamingChunkingEngine(ChunkingEngine):
    def __init__(self, *, strategy='SECTION', level=2, max_chunk_tokens=800,
                 reserve_tokens=64, reader: DocumentReader | None = None, counter=None):
        self.reader = reader or SqliteDocumentReader()
        self.planner = BlockChunker(ChunkBudget(max_chunk_tokens, reserve_tokens, counter),
                                    strategy=strategy, level=level)

    def chunk(self, document):
        with self.reader.open(document.content_path) as source:
            yield from self.planner.chunks(source)
