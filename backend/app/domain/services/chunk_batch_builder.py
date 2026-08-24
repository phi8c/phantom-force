from math import ceil
from uuid import UUID
from uuid import uuid4

from app.domain.entities.chunk import (
    Chunk,
)
from app.domain.entities.chunk_batch import (
    ChunkBatch,
)
from app.domain.entities.document_chunk import (
    DocumentChunk,
)
from app.domain.services.chunk_batch_build_result import (
    ChunkBatchBuildResult,
)


class ChunkBatchBuilder:

    def __init__(
        self,
        batch_size: int = 20,
    ):
        self.batch_size = batch_size

    def build(
        self,
        document_id: UUID,
        chunks: list[
            Chunk
        ],
    ) -> ChunkBatchBuildResult:

        if not chunks:

            return ChunkBatchBuildResult(
                batches=[],
                chunks=[],
            )

        batches: list[
            ChunkBatch
        ] = []

        document_chunks: list[
            DocumentChunk
        ] = []

        total_batches = ceil(
            len(chunks)
            / self.batch_size
        )

        for batch_index in range(
            total_batches,
        ):

            start = (
                batch_index
                * self.batch_size
            )

            end = (
                start
                + self.batch_size
            )

            batch_chunks = chunks[
                start:end
            ]

            batch = ChunkBatch(
                id=uuid4(),
                document_id=document_id,
                batch_index=batch_index,
                total_chunks=len(
                    batch_chunks,
                ),
                
            )

            batches.append(
                batch,
            )

            for chunk in batch_chunks:

                document_chunks.append(
                    DocumentChunk(
                        id=None,
                        batch_id=batch.id,
                        document_id=document_id,
                        chunk_index=chunk.sequence,
                        title=chunk.title,
                        content=chunk.content,
                        metadata=chunk.metadata,
                        
                    )
                )

        return ChunkBatchBuildResult(
            batches=batches,
            chunks=document_chunks,
        )