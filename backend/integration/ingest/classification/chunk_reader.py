from uuid import UUID

from module.ingest.chunking.composition import (
    DocumentChunkQuery,
)
from module.ingest.classification.composition import (
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

    async def iter_by_batch_id(self, batch_id: UUID, *, page_size: int = 32):
        async for chunks in self.chunk_query.iter_by_batch_id(batch_id, page_size=page_size):
            yield [ChunkForClassification(chunk.id, chunk.content, chunk.metadata) for chunk in chunks]

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
