from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.chunking.infrastructure.persistence.models.document_chunk_model import (
    DocumentChunkModel,
)
from module.ingest.chunking.domain.contracts.document_chunk_query import (
    DocumentChunkQuery as DocumentChunkQueryContract,
    DocumentChunkRecord,
)


class DocumentChunkQuery(DocumentChunkQueryContract):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def iter_by_batch_id(self, batch_id: UUID, *, page_size: int = 32):
        if not 1 <= page_size <= 1000:
            raise ValueError('Page size must be between 1 and 1000')
        after = -1
        while True:
            # Select columns rather than retaining ORM instances in the identity map.
            statement = select(DocumentChunkModel.id, DocumentChunkModel.chunk_index,
                               DocumentChunkModel.content, DocumentChunkModel.metadata_payload).where(
                DocumentChunkModel.batch_id == batch_id,
                DocumentChunkModel.chunk_index > after,
            ).order_by(DocumentChunkModel.chunk_index.asc()).limit(page_size)
            rows = (await self.session.execute(statement)).all()
            if not rows:
                return
            after = rows[-1][1]
            yield [DocumentChunkRecord(chunk_id, content, metadata or {})
                   for chunk_id, _, content, metadata in rows]

    async def list_by_batch_id(
        self,
        batch_id: UUID,
    ) -> list[DocumentChunkRecord]:

        statement = (
            select(
                DocumentChunkModel,
            )
            .where(
                DocumentChunkModel.batch_id
                == batch_id,
            )
            .order_by(
                DocumentChunkModel.chunk_index.asc(),
            )
        )

        result = await self.session.execute(
            statement,
        )

        return [
            DocumentChunkRecord(
                id=model.id,
                content=model.content,
                metadata=model.metadata_payload or {},
            )
            for model in result.scalars().all()
        ]
