from dataclasses import dataclass

from app.domain.entities.chunk_batch import (
    ChunkBatch,
)
from app.domain.entities.document_chunk import (
    DocumentChunk,
)


@dataclass(slots=True)
class ChunkBatchBuildResult:

    batches: list[
        ChunkBatch
    ]

    chunks: list[
        DocumentChunk
    ]