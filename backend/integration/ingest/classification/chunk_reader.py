from uuid import UUID

from module.ingest.chunking.domain.contracts.document_chunk_query import (
    DocumentChunkQuery,
)
from module.ingest.classification.domain.contracts.chunk_reader import (
    ChunkForClassification,
    ChunkReader,
)


class ModuleChunkReader(
    ChunkReader,
):

    def __init__(
        self,
        chunk_query: DocumentChunkQuery,
    ):
        self.chunk_query = chunk_query

    async def list_by_batch_id(
        self,
        batch_id: UUID,
    ) -> list[ChunkForClassification]:

        chunks = await self.chunk_query.list_by_batch_id(
            batch_id,
        )

        return [
            ChunkForClassification(
                id=chunk.id,
                content=chunk.content,
                metadata=chunk.metadata,
            )
            for chunk in chunks
        ]
