from uuid import UUID

from module.ingest.chunking.domain.contracts.document_chunk_query import (
    DocumentChunkQuery,
)
from module.ingest.embedding.domain.contracts.chunk_reader import (
    ChunkForEmbedding,
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
    ) -> list[ChunkForEmbedding]:

        chunks = await self.chunk_query.list_by_batch_id(
            batch_id,
        )

        return [
            ChunkForEmbedding(
                id=chunk.id,
                content=chunk.content,
                metadata=chunk.metadata,
            )
            for chunk in chunks
        ]
