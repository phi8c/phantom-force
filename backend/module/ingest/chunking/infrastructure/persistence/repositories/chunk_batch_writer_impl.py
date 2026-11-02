from contextlib import aclosing
from datetime import datetime
from datetime import timezone
from collections.abc import Iterable
from uuid import UUID
from uuid import uuid4

from sqlalchemy import literal
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import insert
from module.ingest.chunking.application.services.async_chunks import iterate_chunks
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.chunking.domain.contracts.chunk_batch_writer import (
    ChunkBatch,
    ChunkBatchWriter,
)
from module.ingest.chunking.domain.contracts.chunking_engine import (
    Chunk,
)
from module.ingest.chunking.infrastructure.persistence.mappers.chunk_batch_mapper import (
    ChunkBatchMapper,
)
from module.ingest.chunking.infrastructure.persistence.models.chunk_batch_model import (
    ChunkBatchModel,
)
from module.ingest.chunking.infrastructure.persistence.models.document_chunk_model import (
    DocumentChunkModel,
)


class ChunkBatchWriterImpl(
    ChunkBatchWriter,
):

    def __init__(
        self,
        session: AsyncSession,
        write_batch_size: int = 100,
    ):
        self.session = session
        if write_batch_size < 1:
            raise ValueError('Chunk write batch size must be positive')
        self.write_batch_size = write_batch_size

    async def get_by_job_and_document(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> ChunkBatch | None:

        statement = select(
            ChunkBatchModel
        ).where(
            ChunkBatchModel.ingestion_job_id
            == ingestion_job_id,
            ChunkBatchModel.document_id
            == document_id,
        )

        result = await self.session.execute(
            statement,
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return ChunkBatchMapper.to_entity(
            model,
        )

    async def create_with_chunks(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        chunks: Iterable[Chunk],
    ) -> ChunkBatch:

        await self._lock_document_batches(
            document_id,
        )

        existing_batch = (
            await self.get_by_job_and_document(
                ingestion_job_id=ingestion_job_id,
                document_id=document_id,
            )
        )

        if existing_batch is not None:
            if existing_batch.total_chunks < 1:
                raise ValueError('Cannot reuse an empty chunk batch')
            return existing_batch

        batch_id = uuid4()
        now = datetime.now(
            timezone.utc,
        )

        batch_model = ChunkBatchModel(
            id=batch_id,
            ingestion_job_id=ingestion_job_id,
            document_id=document_id,
            batch_index=(
                await self._next_batch_index(
                    document_id,
                )
            ),
            total_chunks=0,
            classification_completed=False,
            embedding_completed=False,
            batch_completed=False,
            created_at=now,
            updated_at=now,
        )

        self.session.add(
            batch_model,
        )
        await self.session.flush()

        total_chunks = 0

        rows = []
        async with aclosing(iterate_chunks(chunks)) as stream:
            async for chunk in stream:
                if chunk.index != total_chunks:
                    raise ValueError('Chunk indices must be contiguous and start at zero')
                rows.append(dict(id=uuid4(), batch_id=batch_id, document_id=document_id,
                                 chunk_index=chunk.index, title=chunk.title, content=chunk.content,
                                 metadata_payload=chunk.metadata or {}, created_at=now))
                total_chunks += 1
                if len(rows) >= self.write_batch_size:
                    await self.session.execute(insert(DocumentChunkModel), rows)
                    rows = []

        if not total_chunks:
            raise ValueError('Chunking produced zero chunks; refusing an empty batch')
        if rows:
            await self.session.execute(insert(DocumentChunkModel), rows)

        batch_model.total_chunks = total_chunks

        await self.session.flush()

        return ChunkBatchMapper.to_entity(
            batch_model,
        )

    async def _lock_document_batches(
        self,
        document_id: UUID,
    ) -> None:

        statement = select(
            func.pg_advisory_xact_lock(
                func.hashtextextended(
                    literal(
                        str(
                            document_id,
                        )
                    ),
                    0,
                )
            )
        )

        await self.session.execute(
            statement,
        )

    async def _next_batch_index(
        self,
        document_id: UUID,
    ) -> int:

        statement = select(
            func.max(
                ChunkBatchModel.batch_index
            )
        ).where(
            ChunkBatchModel.document_id
            == document_id,
        )

        result = await self.session.execute(
            statement,
        )

        current_max = result.scalar_one_or_none()

        if current_max is None:
            return 0

        return int(
            current_max
        ) + 1
